# Pychatbot

用於協助 Python 程式設計通識課的同學查詢分數、出席、提問；以及通知總結評分、回饋的 Linebot 後端．

## Issue

### Race condition

此程式可能出現 Race condition。例如上一個請求沒有做完(來不及轉換使用者狀態)，下一個請求又提早開始處理，結果造成錯誤的後果．
