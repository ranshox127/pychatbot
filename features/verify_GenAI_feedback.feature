Feature: 驗證 GenAI 的總結回饋
  身為一位助教
  我希望能驗證 GenAI 對學生總結產生的回饋
  以確保內容正確與合理

  Background:
    Given 學生的總結已完成自動批改
    And 助教開啟了驗證回饋的網頁

  Scenario: 回饋內容沒有問題
    When 助教閱讀了回饋
    And 助教按下「Submit」按鈕
    Then 系統應該記錄回饋確認
    And 系統應該發送批改結果給學生

  Scenario: 回饋需要調整
    When 助教編輯了新的回饋內容並給予評分
    And 助教按下「Submit」按鈕
    Then 系統應該記錄新的回饋與評價
    And 系統應該發送批改結果給學生