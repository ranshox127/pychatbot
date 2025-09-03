import os
import re
from typing import Optional

from openai import OpenAI

from domain.student import StudentRepository
from domain.summary_repositories import GradingLogRepository


class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_content(self, prompt: str, system_role: str, feedback_type: str) -> Optional[str]:
        """
        Generate content based on a prompt and system role.
        Args:
            prompt (str): The user input prompt.
            system_role (str): The system role instruction.
            feedback_type (str): The type of feedback, either "code" or "summary".

        Returns:
            str | None: The generated content if successful; otherwise, None.
        """
        model = "gpt-4o-mini" if feedback_type == "summary" else "gpt-4o"
        try:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                seed=35353
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None


class GenAIFeedbackService:
    def __init__(self, openai_client: OpenAIClient, student_repo: StudentRepository, grading_logs_repo: GradingLogRepository):
        self.openai_client = openai_client
        self.student_repo = student_repo
        self.grading_logs_repo = grading_logs_repo

    def generate_feedback_for_summary(self, stdID: str, contents_name: str, example_summary: str, student_summary: str, summary_grading_log_id: int, basic_feedback: str) -> str:
        user_prompt = self.create_summary_prompt(
            example_summary, student_summary)

        feedback = self.openai_client.generate_content(
            user_prompt, "", feedback_type="summary")
        if feedback is None:
            return "Error generating feedback from GPT."

        suggestions = re.findall(
            r'<suggestion>(.*?)</suggestion>', feedback, re.DOTALL)
        GPT_Feedback = "".join([suggestion.strip()
                               for suggestion in suggestions])

        try:
            student = self.student_repo.find_by_student_id(stdID)
            # Store feedback in database
            return_message = self.grading_logs_repo.write_summary_GPT_feedback_to_verify_db_with_check_repeat(
                stdID, contents_name, GPT_Feedback, student.context_title, student_summary, summary_grading_log_id, basic_feedback, student.line_user_id
            )
            return return_message
        except Exception as e:
            print(f"Error in generating feedback for summary: {e}")
            return "Error in processing feedback."

    def create_summary_prompt(self, example_summary: str, student_summary: str) -> str:
        try:
            # 使用專案根目錄來構建檔案的絕對路徑
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            file_path = os.path.join(
                project_root, 'prompts', 'summary_user_prompt_template.txt')

            with open(file_path, 'r', encoding='utf-8') as file:
                user_prompt_template = file.read()
            return user_prompt_template.format(
                example_summary=example_summary, student_summary=student_summary)
        except Exception as e:
            print(f"Error reading summary prompt template: {e}")
            return ""
