;; -*- lexical-binding: t; -*-
;;
;; Copyright (C) 2025 daniel german (dmg@turingmachine.org)

;; Author: Daniel M German (dmg@turingmachine.org)
;; Created: Feb 15, 2025
;; SPDX-License-Identifier: GPL-3.0-or-later
;; Version: 0.1
;; Homepage: https://github.com/dmgerman/yt-playlist


;; location of script

;;; Code:

(defvar yt-playlist-update-org-script (expand-file-name "~/bin/yt-playlist-update-org.py")
  "location of python script. See installation instructions."
  )

(defun yt-playlist-check-executable (fname)
  "Verify that executable FNAME exists."
  (unless (executable-find fname)
    (error (format "yt-playlist error: executable %s does not exist" fname))))


(defun yt-playlist-update-buffer ()
  "Update the buffer's youtube play lists tables using the script defined
in yt-playlist-update-org-playlist."
  (interactive)
  (yt-playlist-check-executable yt-playlist-update-org-script)

  (let* ((output-buffer (generate-new-buffer "*command-output*"))
         (command (concat (format "%s '%s'" yt-playlist-update-org-script (buffer-file-name))))
         (_ (message  command))
         (exit-code (call-process-shell-command command nil output-buffer )))

    (if (zerop exit-code)
        (progn
          (erase-buffer)
          (insert-buffer-substring output-buffer)
          (kill-buffer output-buffer)
          (message "Buffer replaced with command output."))
      (kill-buffer output-buffer)
      (message "Command failed with exit code: %d" exit-code))))

(provide 'yt-playlist-update)
