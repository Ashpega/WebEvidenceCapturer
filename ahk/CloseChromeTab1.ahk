SetTitleMatchMode(2)  ; ウィンドウタイトルの部分一致を許可
WinActivate("Google Chrome")
Sleep (800)
Send("^w") ; Ctl+Shift+Y（SingleFileの保存ショートカット）