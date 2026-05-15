window.Utils = {
    escapeHTML(text) {
        if (!text) return "";
        return text.replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[m]);
    },

    addBubble(list, content, who, time = null, id = null, showAvatar = false, audioUrl = null) {
        const bubble = document.createElement("div");
        bubble.className = `bubble ${who}`;
        if (id) bubble.dataset.id = id;

        let html = "";

        // رسم مشغل الصوت لو الرسالة عبارة عن فويس نوت
        if (audioUrl) {
            html += `
                <div style="display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.06); padding: 6px 12px; border-radius: 20px; margin-bottom: 6px; min-width: 220px;">
                    <span style="font-size: 18px; color: #007bff;">🎤</span>
                    <audio controls src="${audioUrl}" style="height: 35px; width: 100%; outline: none;"></audio>
                </div>
                <span class="msg" style="font-size: 13px; color: #555; display: block; margin-bottom: 5px;"><i>"${this.escapeHTML(content)}"</i></span>
            `;
        } else {
            // رسم رسالة نصية عادية
            html += `<span class="msg">${this.escapeHTML(content)}</span>`;
        }

        // رسم منطقة الأفاتار لو فيه إشارة
        if (showAvatar) {
            html += `
              <div class="avatar-container" style="margin-top: 8px;">
                 <div class="avatar-placeholder avatar-box" style="padding: 10px; text-align: center; background: #f0f0f0; border-radius: 8px; font-size: 12px; color: #888;">
                    <span>Loading Avatar...</span>
                 </div>
                 <div class="avatar-video-area d-none" style="width: 100%;"></div>
              </div>
            `;
        }

        const deleteBtnHTML = `<div class="delete-msg-btn" title="Delete the message">🗑️</div>`;

        // تجميع الفقاعة بالكامل مع الوقت
        bubble.innerHTML = `
          ${deleteBtnHTML}
          <div class="bubble-content">
            ${html}
            <span class="time">${time || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          </div>
        `;

        // تفعيل زر الحذف عند الضغط على الفقاعة (مع استثناء الضغط على مشغل الصوت)
        bubble.onclick = (e) => {
            if (e.target.classList.contains('delete-msg-btn') || e.target.tagName === 'AUDIO') return;
            document.querySelectorAll('.bubble.active').forEach(b => { if (b !== bubble) b.classList.remove('active'); });
            bubble.classList.toggle('active');
        };

        // منطق مسح الرسالة
        const delBtn = bubble.querySelector('.delete-msg-btn');
        if (delBtn) {
            delBtn.onclick = async (e) => {
                e.stopPropagation();
                if (confirm("Delete the message ?")) {
                    try {
                        await fetch(`/chat/message/${id}/delete/`, { method: "POST", headers: { "X-CSRFToken": CSRF } });
                        bubble.remove();
                    } catch (err) { 
                        console.error(err); 
                    }
                }
            };
        }

        list.appendChild(bubble);
        list.scrollTop = list.scrollHeight;
        return bubble;
    }
};