Feature: 詢問助教流程
  身為一位學生
  我想要透過 Pychatbot 問助教非程式上的問題

  Scenario: 成功完成提問
    Given 我已經註冊並登入系統
    And 我開啟了 Pychatbot 主選單
    When 我點選「我有問題」按鈕
    And 我留下問題
    Then 系統應該記錄我的提問操作