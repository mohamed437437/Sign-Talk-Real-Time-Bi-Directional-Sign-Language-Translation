window.Chat = {
    socket: null,
    activeIframe: null,
    activeContainer: null,
    activePlayBtn: null,

    availableWords: new Set([
        "animal", "answer", "apple", "ask", "aunt", "baby", "bad", "balance",
        "basketball", "bathroom", "bed", "before", "black", "blood", "book",
        "bowling", "brave", "brother", "buy", "call", "clean", "cold", "come",
        "computer", "cook", "cough", "cry", "dad", "danger", "day", "deaf",
        "degree", "delete", "eclipse", "equal", "everyone", "facecream",
        "future", "hello", "my_name_is", "my", "new_year", "or", "please",
        "take", "this", "where", "which", "you"
    ]),

    _buildIframeHTML(wordsArray) {
        const origin = window.location.origin;
        const modelsBase = `${origin}/static/models/`;
        const wordsJson = JSON.stringify(wordsArray);

        return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"><\/script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:100%; height:100%; overflow:hidden; background:#f0f0f0; }
  model-viewer { width:100%; height:100%; background:#f0f0f0; display:block; }
  #badge {
    position:fixed; bottom:8px; left:8px; z-index:10;
    background:rgba(0,0,0,0.7); padding:4px 10px;
    border-radius:15px; display:flex; align-items:center; gap:5px;
  }
  #wlabel { color:#00ff88; font-weight:bold; font-size:14px; font-family:sans-serif; }
  #wcounter { color:#fff; font-size:11px; font-family:sans-serif; }
  #fs-btn {
    position:fixed; top:8px; right:8px; z-index:20;
    background:rgba(0,0,0,0.6); color:white; border:none;
    border-radius:6px; padding:5px 10px; cursor:pointer; font-size:13px;
    font-family:sans-serif;
  }
</style>
</head>
<body>
  <model-viewer id="mv" autoplay camera-controls></model-viewer>
  <div id="badge">
    <span id="wlabel">...</span>
    <span id="wcounter"></span>
  </div>
  <button id="fs-btn">⛶ Fullscreen</button>
<script>
  const mv = document.getElementById('mv');
  const wlabel = document.getElementById('wlabel');
  const wcounter = document.getElementById('wcounter');
  const fsBtn = document.getElementById('fs-btn');
  const words = ${wordsJson};
  const modelsBase = "${modelsBase}";
  let playing = true, tid = null;

  fsBtn.onclick = () => {
    const el = document.documentElement;
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      (el.requestFullscreen || el.webkitRequestFullscreen || function(){}).call(el);
      fsBtn.textContent = '✕ Exit';
    } else {
      (document.exitFullscreen || document.webkitExitFullscreen || function(){}).call(document);
      fsBtn.textContent = '⛶ Fullscreen';
    }
  };
  document.addEventListener('fullscreenchange', () => { if (!document.fullscreenElement) fsBtn.textContent = '⛶ Fullscreen'; });
  document.addEventListener('webkitfullscreenchange', () => { if (!document.webkitFullscreenElement) fsBtn.textContent = '⛶ Fullscreen'; });

  function playWord(i) {
    if (!playing || !words.length) return;
    const w = words[i];
    wlabel.textContent = w.toUpperCase();
    wcounter.textContent = words.length > 1 ? '(' + (i+1) + '/' + words.length + ')' : '';
    mv.src = modelsBase + w + 'Avatar.glb';
    if (words.length === 1) return;
    mv.addEventListener('load', function onLoad() {
      mv.removeEventListener('load', onLoad);
      if (!playing) return;
      tid = setTimeout(() => playWord((i + 1) % words.length), 2800);
    }, { once: true });
  }

  window.addEventListener('DOMContentLoaded', () => { if (words.length > 0) playWord(0); });
  window.addEventListener('message', (e) => {
    if (e.data && e.data.action === 'stop') { playing = false; if (tid) clearTimeout(tid); mv.src = ''; }
  });
<\/script>
</body>
</html>`;
    },

    init({ list, otherUserId }) {
        const wsScheme = location.protocol === "https:" ? "wss" : "ws";
        this.socket = new WebSocket(`${wsScheme}://${location.host}/ws/chat/${otherUserId}/`);
        this._otherUserId = String(otherUserId);

        this.socket.onopen = () => {
            console.log("✅ WebSocket Connected");
            this.sendStatus("online");
        };

        this.socket.onclose = () => { this.updateStatusUI(false); };
        window.addEventListener('beforeunload', () => this.sendStatus("offline"));

        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            if (data.type === 'user_status') {
                if (String(data.user_id) === this._otherUserId) {
                    this.updateStatusUI(data.status === 'online');
                }
                return;
            }

            if (data.message) {
                const isMe = (data.sender_id == CURRENT_USER_ID);
                const who = isMe ? "me" : "bot";
                const senderType = data.sender_type || "normal"; // "deaf" أو "normal"

                let cleanMsg = data.message;
                let showAvatar = false;
                let wordsToPlay = [];
                let audioUrl = null;
                let isDeafMessage = false;

                // ✅ رسالة من أصم (فيها ||CAM||)
                if (cleanMsg.includes("||CAM||")) {
                    isDeafMessage = true;
                    cleanMsg = cleanMsg.replace(" ||CAM||", "").replace("||CAM||", "");
                }

                // ✅ رسالة فيها VOICE
                if (cleanMsg.startsWith("[VOICE]")) {
                    let parts = cleanMsg.split("|");
                    if (parts.length > 1) {
                        audioUrl = parts[0].replace("[VOICE]", "");
                        cleanMsg = parts.slice(1).join("|");
                    }
                }

                // ✅ رسالة فيها SIGN
                if (cleanMsg.startsWith("[SIGN]")) {
                    let parts = cleanMsg.split("|");
                    if (parts.length > 1) {
                        let signPart = parts[0].replace("[SIGN]", "");
                        cleanMsg = parts[1];

                        // ✅ الأفاتار بيظهر فقط لو المرسل عادي (مش أصم) وأنا مش المرسل
                        if (!isMe && !isDeafMessage) {
                            showAvatar = true;
                            wordsToPlay = signPart.split(",").map(w => w.trim());
                        }
                    }
                } else if (!isDeafMessage) {
                    // ✅ نص عادي من شخص عادي - دور على كلمات الأفاتار
                    if (!isMe) {
                        let found = cleanMsg.toLowerCase().split(/\s+/).filter(w => this.availableWords.has(w));
                        if (found.length > 0) { showAvatar = true; wordsToPlay = found; }
                    }
                }

                // ✅ لو رسالة من أصم → عرض النص بس بدون أفاتار
                // ✅ لو رسالة من عادي → عرض الأفاتار بدون نص (أو بالنص لو مفيش أفاتار)
                const bubble = Utils.addBubble(list, cleanMsg, who, data.time, data.id, showAvatar, audioUrl);
                if (showAvatar && bubble) this._scheduleSetup(wordsToPlay, bubble, true);
            }
        };

        this.loadHistory(list);
    },

    _scheduleSetup(wordsArray, bubble, isAutoPlay) {
        const run = () => this._setupAvatarBubble(wordsArray, bubble, isAutoPlay);
        if ('requestIdleCallback' in window) {
            requestIdleCallback(run, { timeout: 2000 });
        } else {
            setTimeout(run, 300);
        }
    },

    stopAllAvatars() {
        if (this.activeIframe) {
            try { this.activeIframe.contentWindow.postMessage({ action: 'stop' }, '*'); } catch (_) {}
        }
        if (this.activeContainer) {
            this.activeContainer.classList.add('d-none');
            this.activeContainer.innerHTML = '';
        }
        if (this.activePlayBtn) this.activePlayBtn.classList.remove('d-none');
        this.activeIframe = null;
        this.activeContainer = null;
        this.activePlayBtn = null;
    },

    _setupAvatarBubble(wordsArray, bubble, isAutoPlay) {
        if (!wordsArray || wordsArray.length === 0) return;

        const placeholder = bubble.querySelector('.avatar-placeholder');
        const videoArea = bubble.querySelector('.avatar-video-area');
        if (!videoArea) return;

        if (placeholder) placeholder.classList.add('d-none');
        videoArea.classList.remove('d-none');

        const uid = bubble.dataset.id || (Date.now() + Math.floor(Math.random() * 1000));

        videoArea.innerHTML = `
            <div id="play-btn-${uid}"
                 style="width:280px;max-width:100%;height:200px;background:#e9ecef;border-radius:8px;
                        display:flex;flex-direction:column;align-items:center;justify-content:center;
                        cursor:pointer;border:2px dashed #ccc;transition:0.3s;margin:10px 0;">
                <span style="font-size:40px;">▶️</span>
                <span style="margin-top:10px;font-weight:bold;color:#555;">Play Sign (${wordsArray.length})</span>
            </div>
            <div id="player-${uid}" class="d-none"
                 style="position:relative;width:280px;height:250px;max-width:100%;
                        background:#f0f0f0;border-radius:8px;overflow:hidden;margin:10px 0;">
            </div>
        `;

        const playBtn = videoArea.querySelector(`#play-btn-${uid}`);
        const playerDiv = videoArea.querySelector(`#player-${uid}`);

        playBtn.addEventListener('click', (e) => { e.stopPropagation(); startPlaying(); });
        playerDiv.addEventListener('click', (e) => { e.stopPropagation(); });

        const startPlaying = () => {
            this.stopAllAvatars();
            playBtn.classList.add('d-none');
            playerDiv.classList.remove('d-none');

            const iframe = document.createElement('iframe');
            iframe.srcdoc = this._buildIframeHTML(wordsArray);
            iframe.setAttribute('allowfullscreen', '');
            iframe.setAttribute('allow', 'fullscreen');
            iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms');
            iframe.style.cssText = 'width:100%;height:100%;border:none;border-radius:8px;display:block;';

            playerDiv.appendChild(iframe);
            this.activeIframe = iframe;
            this.activeContainer = playerDiv;
            this.activePlayBtn = playBtn;
        };

        if (isAutoPlay) {
            if ('IntersectionObserver' in window) {
                const obs = new IntersectionObserver((entries) => {
                    if (entries[0].isIntersecting) { obs.disconnect(); startPlaying(); }
                }, { threshold: 0.3 });
                obs.observe(bubble);
            } else {
                setTimeout(startPlaying, 200);
            }
        }
    },

    loadHistory(list) {
        const el = document.getElementById("initial-messages");
        if (!el || !el.textContent.trim()) return;

        setTimeout(() => {
            try {
                const msgs = JSON.parse(el.textContent);
                list.innerHTML = '<div class="wa-day">Today</div>';
                const recent = msgs.slice(-20);

                const renderBatch = (startIdx) => {
                    const end = Math.min(startIdx + 5, recent.length);
                    for (let i = startIdx; i < end; i++) {
                        const m = recent[i];
                        let content = m.message;
                        const isMe = (m.sender_id == CURRENT_USER_ID);
                        const who = isMe ? "me" : "bot";
                        let showAvatar = false, wordsToPlay = [], audioUrl = null;
                        let isDeafMessage = false;

                        if (content.includes("||CAM||")) {
                            isDeafMessage = true;
                            content = content.replace(" ||CAM||", "").replace("||CAM||", "");
                        }

                        if (content.startsWith("[VOICE]")) {
                            let parts = content.split("|");
                            if (parts.length > 1) { audioUrl = parts[0].replace("[VOICE]", ""); content = parts.slice(1).join("|"); }
                        }

                        if (content.startsWith("[SIGN]")) {
                            let parts = content.split("|");
                            if (parts.length > 1) {
                                wordsToPlay = parts[0].replace("[SIGN]", "").split(",").map(w => w.trim());
                                content = parts[1];
                                if (!isMe && !isDeafMessage) showAvatar = true;
                            }
                        } else if (!isDeafMessage && !isMe) {
                            let found = content.toLowerCase().split(/\s+/).filter(w => this.availableWords.has(w));
                            if (found.length > 0) { showAvatar = true; wordsToPlay = found; }
                        }

                        const bubble = Utils.addBubble(list, content, who, m.time, m.id, showAvatar, audioUrl);
                        if (showAvatar && bubble) this._scheduleSetup(wordsToPlay, bubble, false);
                    }
                    if (end < recent.length) {
                        requestAnimationFrame(() => renderBatch(end));
                    } else {
                        list.scrollTop = list.scrollHeight;
                    }
                };
                renderBatch(0);
            } catch (err) { console.error("History Error:", err); }
        }, 300);
    },

    sendStatus(status) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: "status_signal", status: status }));
        }
    },

    updateStatusUI(isOnline) {
        const el = document.getElementById("userStatus");
        if (el) {
            el.textContent = isOnline ? "Online" : "Offline";
            el.className = isOnline ? "status-online" : "status-offline";
        }
    },

    send(text) {
        if (!text) return;
        fetch('/chat/agent/process/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: "text_to_sign", message: text })
        })
        .then(r => r.json())
        .then(data => {
            let msg = text;
            if (data.status === "success" && data.animation_sequence?.length > 0) {
                const words = data.animation_sequence.map(i => i.word).join(",");
                msg = `[SIGN]${words}|${text}`;
            }
            if (this.socket?.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ message: msg }));
            }
        })
        .catch(() => {
            if (this.socket?.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ message: text }));
            }
        });
    }
};