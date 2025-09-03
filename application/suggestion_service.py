from typing import List
from domain.summary_repositories import SuggestionQueryRepository


class SuggestionService:
    def __init__(self, suggestion_repo: SuggestionQueryRepository):
        self.suggestion_repo = suggestion_repo

    def produce(self, stdID, context_title, contents_name):
        """
        從最新評分紀錄組建建議訊息。
        - 無紀錄：回穩健的預設訊息（不主動觸發評分）
        - 字數不足/未寫：回對應提示
        - 通過且無缺字：兩種語氣（penalty=1 表示精簡？沿用你的規則）
        - 其餘：列出缺失關鍵字對應問題
        """
        last = self.suggestion_repo.get_suggestion_info(
            stdID, context_title, contents_name)
        if not last:
            return "目前找不到你的評分紀錄，請稍後再嘗試或聯絡助教。"
        try:
            kws, questions = self.suggestion_repo.get_questions(
                context_title, contents_name)
            kw2q = {k: q for k, q in zip(kws, questions)}

            summary = last.get("summary")
            penalty = last.get("penalty")
            result = last.get("result")
            loss_kw: List[str] = last.get("loss_kw") or []
            loss_concept_kws: List[str] = last.get("loss_concept_kws") or []

            # 未寫
            if summary in (None, "None"):
                return f"你 {contents_name} 的總結還沒有寫喔 QAQ\n寫完後可以點選重新評分，TA 會盡快幫你批改的!"

            # 字數不足
            if penalty == -1:
                return f"同學你好，你 {contents_name} 的總結字數不足 20 字，會視為缺交！\n補寫完成後可以點選重新評分，TA 會盡快幫你批改的!"

            # 通過且無缺字與觀念缺字
            if not loss_kw and not loss_concept_kws and result == 1:
                if penalty == 1:
                    return f"同學你好，你的 {contents_name} 總結評分為 [通過]，寫得很棒，請繼續保持喔!"
                else:
                    return f"同學你好，你的 {contents_name} 總結評分為 [通過]，內容也都很完整，不過還可以再稍微精簡一點喔!"

            # 其餘：組建建議與題目
            suggestion_lines: List[str] = []
            if result == 0:
                suggestion_lines.append(
                    f"同學你好，你的 {contents_name} 總結評分為 [不通過]，修改建議如下：")
            else:
                suggestion_lines.append(
                    f"同學你好，你的 {contents_name} 總結評分為 [通過]，但依然有一些修改建議要給你：")

            if loss_kw:
                suggestion_lines.append("\n你的總結中缺少了一些重要的關鍵字，以下是關於缺失關鍵字的提示：")
                idx = 1
                for kw in loss_kw:
                    q = kw2q.get(kw)
                    if q:
                        suggestion_lines.append(f"{idx}. {q}")
                        idx += 1

            suggestion_lines.append(
                "\n缺失的關鍵字可以藉由回答問題的方式將總結的內容補齊全，加油加油，改完後按重新評分，TA 會幫你再次批改的！\n\n下方有總結回饋，同學可以參考並添加總結內容："
            )
            return "\n".join(suggestion_lines)

        except Exception as e:
            return "發生了一些問題，可能是因為網路問題或是系統繁忙，請稍後再嘗試。"
