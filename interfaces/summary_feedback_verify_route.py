import os
from flask import jsonify, render_template, request

from flask import Blueprint
from dependency_injector.wiring import inject, Provide
import pymysql
from containers import AppContainer
from domain.feedback import FeedbackRepository
from infrastructure.gateways.line_api_service import LineApiService

summary_feedback_verify_bp = Blueprint('summary_feedback_verify', __name__)


@summary_feedback_verify_bp.route('/summarysubmissions/')
@inject
def summarysubmissions_web():
    """回傳 html 模板. 模板在 /templates"""
    return render_template('SummarySubmission.html')


@summary_feedback_verify_bp.route('/api/summarysubmissions', methods=['GET'])
@inject
def summarysubmissions(feedback_repo: FeedbackRepository = Provide[AppContainer.feedback_repo]):
    """
    在回傳模板之後，網頁會向後端要資料。
    此函式位於 templates/SummarySubmission.html 的 document.addEventListener('DOMContentLoaded') callback
    """
    submissions = feedback_repo.get_summarysubmissions()
    return jsonify(submissions)


@summary_feedback_verify_bp.route('/api/summarysubmissions/<submission_id>', methods=['PUT'])
@inject
def update_summary_submission_status(submission_id, feedback_repo: FeedbackRepository = Provide[AppContainer.feedback_repo]):
    """
    按下 Save 之後，更新這個feedback的狀態。 具體來說，狀態會從'wait_review'變成'complete_review'
    """
    try:
        feedback_repo.complete_review_summarysubmission(submission_id)
        return jsonify({"message": "SummarySubmissions status updated"}), 200
    except pymysql.MySQLError as err:
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500


@summary_feedback_verify_bp.route('/api/teacherfeedbacks', methods=['POST'])
@inject
def insert_teacher_feedback(feedback_repo: FeedbackRepository = Provide[AppContainer.feedback_repo]):
    """按下 Save 之後就會把改完的 Feedback 丟回去 db"""
    data = request.get_json()

    required_keys = ['SubmissionId', 'SubmissionType',
                     'Feedback', 'FeedbackTime', 'context_title', 'LineID']
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return jsonify({"error": f"Missing keys in the request: {missing_keys}"}), 400

    try:
        feedback_id = feedback_repo.insert_teacher_feedback(
            data['SubmissionId'], data['SubmissionType'], data['Feedback'], data['FeedbackTime'], data['context_title'], data['LineID'])
        return jsonify({"FeedbackId": feedback_id}), 200
    except pymysql.MySQLError as err:
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500


@summary_feedback_verify_bp.route('/api/feedbackevaluations', methods=['POST'])
@inject
def insert_feedback_evaluation(feedback_repo: FeedbackRepository = Provide[AppContainer.feedback_repo]):
    """根據不同的 feedback 類型，將數據插入到對應的資料表中"""
    data = request.get_json()
    required_keys = ['FeedbackId', 'Accuracy', 'Readability',
                     'Clarity', 'Consistency', 'Answerability']
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

    feedback_type = data.get('type')  # 假設前端會傳遞 'type' 參數 ('summary' 或 'code')

    try:
        if feedback_type == 'summary':
            evaluation_id = feedback_repo.insert_summary_feedback_evaluation(
                data['FeedbackId'], data['Accuracy'], data['Readability'], data['Clarity'], data['Consistency'], data['Answerability'])
            return jsonify({"EvaluationId": evaluation_id}), 200

        elif feedback_type == 'code':
            pass
            # insert_query = """
            #     INSERT INTO FeedbackEvaluations_v2 (
            #         FeedbackId, execution_result, correctness_rate, adheres_section_scope,
            #         personalized_modifications, suggestion_correctness, suggestion_completeness,
            #         suggestion_without_code, consistent_suggestions, remarks
            #     )
            #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # """
            # # 插入 code 類型的數據
            # cursor.execute(insert_query, (
            #     data['FeedbackId'],
            #     data['execution_result'],
            #     data['correctness_rate'],
            #     data['adheres_section_scope'],
            #     data['personalized_modifications'],
            #     data['suggestion_correctness'],
            #     data['suggestion_completeness'],
            #     data['suggestion_without_code'],
            #     data['consistent_suggestions'],
            #     data['remarks']
            # ))

        else:
            return jsonify({"error": "Unknown feedback type"}), 400

    except pymysql.MySQLError as err:
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500


@summary_feedback_verify_bp.route('/api/send-feedback/', methods=['POST'])
@inject
def send_feedback(line_service: LineApiService = Provide[AppContainer.line_api_service]):
    """按下 Save 之後就會把改完的 Feedback 透過 line 回傳給學生"""
    data = request.get_json()
    line_user_id = data['line_userID']
    feedback = data['feedback']

    try:
        line_service.push_message(line_user_id, [feedback])
        return jsonify({"message": "Feedback sent successfully"}), 200

    except Exception as e:
        print(f"Line API send error: {e}")
        return jsonify({"error": str(e)}), 500
