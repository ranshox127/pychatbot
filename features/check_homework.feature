Feature: 學生查看單元分數
  身為一位學生
  我想要透過 Pychatbot 查看某單元的 OJ 與總結分數

  Background:
    Given 我已經註冊並登入系統
    And 我開啟了 Pychatbot 主選單

  Scenario: 查詢已開放且存在的單元
    When 我點選「作業繳交查詢」按鈕
    And 我輸入了存在的單元名稱 "C4"
    Then 系統應該查詢該單元成績
    And 系統應該傳送作業的分數給我
    And 系統應該記錄我的查詢事件

  Scenario: 尚未有任何開放的單元
    When 我點選「作業繳交查詢」按鈕
    Then 系統應該通知我「目前還沒有任何要繳交的作業喔。」

  Scenario: 查詢不存在的單元
    When 我輸入了不存在的單元名稱 "C9"
    Then 系統應該通知我「請單元名稱不存在，請確認後再重新查詢喔。」
