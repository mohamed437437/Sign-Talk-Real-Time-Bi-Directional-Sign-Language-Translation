// static/js/ai.js

async function sendToAI(text) {
    const chatBox = document.getElementById('chatBox');
    
    // إظهار رسالة المستخدم
    addMessage(text, 'user');

    // إظهار تحميل
    const loading = document.createElement('div');
    loading.className = 'text-center text-info';
    loading.textContent = 'جاري التحليل...';
    chatBox.appendChild(loading);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch('/api/ai-sign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        loading.remove();

        if (data.video_url) {
            showSignVideo(data.label || text, data.video_url);
        } else {
            addMessage("لا يمكن تحويل هذه الجملة حاليًا.", 'system');
        }
    } catch (err) {
        loading.remove();
        addMessage("فشل في الاتصال بالذكاء الاصطناعي.", 'system');
    }
}

// دالة إضافة رسالة
function addMessage(text, sender) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'text-end mb-2' : 'text-start mb-2';
    
    const msg = document.createElement('div');
    msg.className = sender === 'user' ? 'd-inline-block bg-primary text-white px-3 py-1 rounded-pill' : 
                                         'd-inline-block bg-light text-dark px-3 py-1 rounded';
    msg.textContent = text;
    
    messageDiv.appendChild(msg);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// عرض فيديو الإشارة
function showSignVideo(label, videoUrl) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'mb-3 text-start';

    const labelSpan = document.createElement('small');
    labelSpan.className = 'text-muted';
    labelSpan.textContent = `إشارة: ${label}`;
    messageDiv.appendChild(labelSpan);

    const video = document.createElement('video');
    video.src = videoUrl;
    video.controls = true;
    video.style.width = '220px';
    video.style.borderRadius = '8px';
    video.style.display = 'block';
    video.style.marginTop = '4px';

    messageDiv.appendChild(video);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}