class CheckScoreService:
    def __init__(self):
        pass

    def check_publish_contents(self):
        pass
        # student = self.student_repo.find_by_line_id(user_id)
        # course = self.course_repo.get_course()
        # if course.publish_contents == []:
        #    self.line_service
        #    return
        # self.line_service
        # self.state_manager.set_state(user_id, UserStateEnum.AWAITING_CONTENTS_NAME)

    def check_score(self):
        pass
        # student = self.student_repo.find_by_line_id(user_id)
        # course = self.course_repo.get_course()
        # if target_content not in course.publish_contents:
        #    self.line_service
        #    return

        # OJ_info = self.OJ_repo.get_OJ_info(student, course, target_content)
        # mistake_review_value = self._get_mistake_review_value()
        # self.line_service

    def _get_mistake_review_value(self, stdID: str, contents_name: str):
        """
        查詢指定學生在某單元（週次）的錯誤回顧成績。

        此函式從 Google Sheets 讀取學生成績數據，根據姓名 `name` 和單元 `contents_name`
        查找對應的錯誤回顧成績，並返回三種可能的結果：
        - 0: 錯誤回顧成績為 0
        - 100: 錯誤回顧成績為 100
        - "無成績": 該欄位數值非 0 或 100，通常代表成績尚未計算完成
        - "沒有找到對應的欄位": 若找不到與 `contents_name` 對應的欄位

        參數:
        - stdID (str): 學號
        - contents_name (str): 目標單元名稱（如 'C1', 'C8'）

        回傳:
        - int: 0 或 100，代表錯誤回顧成績
        - str: "無成績" 或 "沒有找到對應的欄位"

        例外處理:
        - 若 `sheet_url` 無效，會輸出 "無效的 Google Sheets 連結"

        範例:
        >>> get_mistake_review_value("jz1452896", "C1")
        100

        >>> get_mistake_review_value("108504510", "C8")
        "無成績"

        >>> get_mistake_review_value("123456789", "C5")
        "沒有找到對應的欄位"
        """
        sheet_url = 'https://docs.google.com/spreadsheets/d/1izTp3WSSdTGxd3Ul65qWU3rwujLTMuE0PIP3rxllvuY/edit?gid=576676265#gid=576676265'

        sheet_id_match = re.search(
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        gid_match = re.search(r"gid=([0-9]+)", sheet_url)

        if not (sheet_id_match and gid_match):
            print("無效的 Google Sheets 連結")

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_match.group(1)}/export?format=csv&gid={gid_match.group(1)}"
        df = pd.read_csv(csv_url)

        # 找到包含 contents_name 的欄位
        matched_columns = [col for col in df.iloc[:,
                                                  4:].columns if f"({contents_name})" in col]

        # 回傳對應數據
        if matched_columns:
            value = df.loc[df['id'] == stdID, matched_columns].values
            if value[0][0] == 0 or value[0][0] == 100:
                return value[0][0]
            else:
                return "無成績"
        return "沒有找到對應的欄位"
