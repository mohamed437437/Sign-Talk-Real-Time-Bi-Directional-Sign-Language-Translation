document.addEventListener("DOMContentLoaded", () => {
    const el = {
        list: document.getElementById("waMessages"),
        box: document.getElementById("msgBox"),
        send: document.getElementById("sendBtn"),
        menuBtn: document.getElementById("menuBtn"),
        menuBox: document.getElementById("menuBox"),
        clearChatBtn: document.getElementById("clearChat"),
        micBtn: document.getElementById("micBtn"), 
        plusBtn: document.getElementById("plusBtn"),
        attachMenu: document.getElementById("attachMenu"),
        uploadAction: document.getElementById("uploadAction"),
        cameraAction: document.getElementById("cameraAction"),
        fileInput: document.getElementById("fileInput"),
        camContainer: document.getElementById("cameraContainer"),
        preview: document.getElementById("preview"),
        startBtn: document.getElementById("startRecordBtn"),
        stopBtn: document.getElementById("stopRecordBtn"),
        closeCam: document.getElementById("closeCamBtn"),
        switchCam: document.getElementById("switchCamBtn"),
        timer: document.getElementById("timer")
    };

    if (el.box && el.micBtn && el.send) {
        el.box.addEventListener("input", function() {
            if (this.value.trim().length > 0) {
                el.micBtn.classList.add("d-none");
                el.send.classList.remove("d-none");
            } else {
                el.micBtn.classList.remove("d-none");
                el.send.classList.add("d-none");
            }
        });
    }

    if (el.plusBtn && el.attachMenu) {
        el.plusBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            el.attachMenu.classList.toggle("d-none");
        });
        document.addEventListener("click", (e) => {
            if (!el.plusBtn.contains(e.target) && !el.attachMenu.contains(e.target)) {
                el.attachMenu.classList.add("d-none");
            }
        });
    }

    if (el.uploadAction && el.fileInput) {
        el.uploadAction.addEventListener("click", () => {
            el.fileInput.click();
            el.attachMenu.classList.add("d-none");
        });
    }

    if (el.cameraAction && el.camContainer) {
        el.cameraAction.addEventListener("click", async () => {
            el.attachMenu.classList.add("d-none");
            el.camContainer.classList.remove("d-none");
            
            if (window.Camera) {
                try {
                    if (!window.isCameraInitialized) {
                        Camera.init({
                             CSRF: CSRF, 
                             el: el,
                             onResult: (wordsArray) => {
                                 fetch('/chat/agent/process/', {
                                     method: 'POST',
                                     headers: { 'Content-Type': 'application/json' },
                                     body: JSON.stringify({ 
                                         type: "sign_to_text", 
                                         words: Array.isArray(wordsArray) ? wordsArray : wordsArray.split(" "),
                                         confidence: 0.85 
                                     })
                                 })
                                 .then(response => response.json())
                                 .then(data => {
                                     if (data.status === "success" && window.Chat && window.Chat.socket.readyState === 1) {
                                         window.Chat.send(data.message + " ||CAM||");
                                     } else {
                                         Utils.addBubble(el.list, data.message, "bot");
                                     }
                                 }).catch(err => {
                                     if(window.Chat && window.Chat.socket.readyState === 1) {
                                         const fallbackMsg = Array.isArray(wordsArray) ? wordsArray.join(" ") : wordsArray;
                                         window.Chat.send(fallbackMsg + " ||CAM||");
                                     }
                                 });
                             }
                        });
                        window.isCameraInitialized = true;
                    }
                    await window.Camera.startStream(el);
                } catch (err) {
                    alert("❌ مش قادر أوصل للكاميرا، اتأكد من الصلاحيات.");
                    el.camContainer.classList.add("d-none");
                }
            }
        });
    }

    if (el.menuBtn && el.menuBox) {
        el.menuBtn.onclick = (e) => {
            e.stopPropagation();
            el.menuBox.classList.toggle("show");
            el.menuBtn.classList.toggle("active");
        };
        document.addEventListener("click", (e) => {
            if (!el.menuBox.contains(e.target) && e.target !== el.menuBtn) {
                el.menuBox.classList.remove("show");
                el.menuBtn.classList.remove("active");
            }
        });
    }

    if (window.Chat) {
        window.Chat.init({ list: el.list, otherUserId: OTHER_USER_ID });
    }

    if (el.send) {
        el.send.onclick = () => {
            const txt = el.box.value.trim();
            if (txt && window.Chat) {
                window.Chat.send(txt);
                el.box.value = "";
                el.micBtn.classList.remove("d-none");
                el.send.classList.add("d-none");
            }
        };
    }
    
    if (el.box) {
        el.box.addEventListener("keypress", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                el.send.click();
            }
        });
    }

    if (el.clearChatBtn) {
        el.clearChatBtn.onclick = async () => {
            if(confirm("Are you sure you want to delete the entire conversation?")) {
                await fetch(`/chat/${OTHER_USER_ID}/clear/`, {method:"POST", headers:{"X-CSRFToken":CSRF}});
                el.list.innerHTML = '<div class="wa-day">Today</div>';
                el.menuBox.classList.remove("show");
                el.menuBtn.classList.remove("active");
                if (window.Chat) window.Chat.stopAllAvatars();
            }
        };
    }

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    if (el.micBtn) {
        el.micBtn.onclick = async () => {
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    isRecording = true;
                    
                    el.micBtn.style.backgroundColor = "#ff4d4d";
                    el.micBtn.style.color = "white";
                    el.micBtn.innerText = "⏹️"; 
                    
                    mediaRecorder.ondataavailable = e => {
                        if (e.data.size > 0) audioChunks.push(e.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        audioChunks = [];
                        
                        const formData = new FormData();
                        formData.append("audio", audioBlob, "voice.webm");
                        
                        el.micBtn.innerText = "⏳";
                        
                        try {
                            const response = await fetch('/chat/api/process-voice/', { 
                                method: 'POST',
                                headers: { 'X-CSRFToken': CSRF },
                                body: formData
                            });
                            
                            const data = await response.json();
                            if (data.status === "success" && data.text && data.audio_url) {
                                const agentRes = await fetch('/chat/agent/process/', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ type: "text_to_sign", message: data.text })
                                });
                                const agentData = await agentRes.json();
                                
                                let msgToSend = `[VOICE]${data.audio_url}|${data.text}`;
                                if (agentData.status === "success" && agentData.animation_sequence && agentData.animation_sequence.length > 0) {
                                    const avatarWords = agentData.animation_sequence.map(item => item.word).join(",");
                                    msgToSend = `[VOICE]${data.audio_url}|[SIGN]${avatarWords}|${data.text}`;
                                }
                                
                                if (window.Chat && window.Chat.socket?.readyState === WebSocket.OPEN) {
                                    window.Chat.socket.send(JSON.stringify({ message: msgToSend }));
                                }
                            } else {
                                alert("Sorry, couldn't understand the audio.");
                            }
                        } catch(e) {
                            console.error("Voice Note Error:", e);
                        } finally {
                            el.micBtn.style.backgroundColor = "";
                            el.micBtn.style.color = "";
                            el.micBtn.innerText = "🎤";
                        }
                    };
                } catch (err) {
                    alert("❌ Cannot access the microphone. Please check permissions.");
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                mediaRecorder.stream.getTracks().forEach(t => t.stop());
            }
        };
    }

    // إخفاء السلة عند الضغط في أي مكان فاضي
    document.addEventListener("click", (e) => {
        if (!e.target.closest('.bubble')) {
            document.querySelectorAll('.bubble.active').forEach(b => {
                b.classList.remove('active');
            });
        }
    });

    // منع ظهور السلة عند الضغط على مشغل الصوت أو أزرار الميديا
    document.addEventListener("click", (e) => {
        const isMediaElement = e.target.closest('audio, video, button, [class*="play"]');
        if (isMediaElement && e.target.closest('.bubble')) {
            e.stopPropagation(); 
        }
    }, true); 

});