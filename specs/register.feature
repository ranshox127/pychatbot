Feature: 學生註冊與綁定身份
  身為一位學生
  我希望能完成帳號註冊與課程綁定
  以便使用 Pychatbot 功能

  Scenario: 成功註冊與綁定課程
    Given 我是尚未註冊的新學生
    When 我輸入正確的學號
    Then 系統應該確認該學號尚未被註冊
    And 系統應該查詢我所屬的課程
    And 系統應該綁定我的 LINE 帳號與課程
    And 系統應該回應歡迎訊息
    And 系統應該切換選單畫面到主選單

  Scenario: 學號已被其他帳號使用
    Given 我是尚未註冊的新學生
    When 我輸入已被其他人註冊的學號
    Then 系統應該提示我「此學號已被其他 Line 帳號使用，請洽詢助教。」

  Scenario: 輸入無效學號
    Given 我是尚未註冊的新學生
    When 我輸入不存在於教學平台的學號
    Then 系統應該提示我「在教學平台上找不到這個學號，請確認後再試一次。」

  Scenario: 已註冊學生重新加好友
    Given 我之前已經註冊過，但更換了 LINE 帳號或解除綁定
    When 我再次加回 Pychatbot 為好友
    Then 系統應該辨識我為已註冊學生
    And 系統應該自動切換至主選單