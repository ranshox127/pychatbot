class CheckAttendanceService:
    def __init__(self):
        pass

    def check_attendance(self, user_id):
        # student = self.student_repo.find_by_line_id(user_id)
        # course = self.course_repo.get_course(student.context_title)
        # absence_info = self._fetch_absence_info_by_name(student.name, course.attendance_url)
        # absence_text = format_absence_info_to_text(absence_info)

        # self.line_service
        # self.event_repo.save_event()

    def _fetch_absence_info_by_name(name, sheet_url):
        # Fetch all data from Google Sheet
        # 使用正則表達式提取sheet_id和gid
        sheet_id_match = re.search(
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        gid_match = re.search(r"gid=([0-9]+)", sheet_url)

        if sheet_id_match and gid_match:
            sheet_id = sheet_id_match.group(1)
            gid = gid_match.group(1)
            # 舊的CSV下載URL
            # csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"

            # 組合成CSV下載URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            print(csv_url)
        else:
            print("Invalid URL")

        df = pd.read_csv(csv_url)
        print(df.iloc[:, [0, 1, 6, 7]])
        # Filter the DataFrame to find rows where the 'name' column matches the given name
        filtered_df = df[df['name'] == name]

        # Convert the filtered DataFrame to a dictionary
        result_dict = filtered_df.to_dict(orient='records')

        # If the name was found, return the first matching row as a dictionary
        if result_dict:
            return result_dict[0]
        else:
            return f"No records found for name: {name}"

    def _format_absence_info_to_text(absence_info):
        print(type(absence_info))  # 打印absence_info的類型
        print(absence_info)  # 打印absence_info的
        if not absence_info or "name" not in absence_info:
            return "無效的缺席信息"

        name = absence_info["name"]
        message = f"{name} 你好，你在以下日期有缺席紀錄:\n"

        has_absence = False
        for date, status in absence_info.items():
            if date not in ["id", "name", "department", "grade"] and pd.notna(status):
                message += f"{date}: {status}\n"
                has_absence = True

        if not has_absence:
            message = f"{name} 你好，你沒有缺席紀錄。"

        return message
