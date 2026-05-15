console.log("📷 camera_new.js LOADED (FINAL FIXED VERSION)");

window.Camera = {
  stream: null,
  recorder: null,
  chunks: [],
  container: null,
  useFront: true, // true للكاميرا الأمامية
  timerInterval: null,

  init({ CSRF, el, onResult }) {
    this.container = el.camContainer;

    // 1. زر فتح الكاميرا
    if (el.openCam) {
        el.openCam.onclick = async () => {
            try {
                this.container.classList.remove("d-none"); // إظهار الحاوية
                await this.startStream(el);
            } catch (err) {
                console.error("Camera Access Error:", err);
                alert("❌ Cannot access the camera. Make sure permissions are granted.");
            }
        };
    }

    // 2. زر بدء التسجيل
    if (el.startBtn) {
        el.startBtn.onclick = () => {
            if (!this.stream) return;
            this.chunks = [];
            
            try {
                this.recorder = new MediaRecorder(this.stream);
            } catch (e) {
                alert("The browser does not support recording");
                return;
            }

            this.recorder.ondataavailable = (e) => {
                if (e.data.size > 0) this.chunks.push(e.data);
            };

            this.recorder.onstop = async () => {
                this.stopTimer(el);
                this.closeCamera(el); // إغلاق الكاميرا وتغيير الأزرار فوراً
                
                // إظهار تنبيه للمستخدم أننا نعالج الفيديو
                // (اختياري، لكن يطمئن المستخدم)
                
                // إرسال الفيديو للسيرفر
                const sentence = await this.sendVideo(CSRF);
                
                // إرسال النتيجة للشات فقط إذا كانت جملة صحيحة
                if (sentence && onResult) {
                    onResult(sentence);
                }
            };

            this.recorder.start();
            
            // تحديث الواجهة (إخفاء زر التسجيل وإظهار زر الإيقاف والوقت)
            el.startBtn.classList.add("d-none");
            el.stopBtn.classList.remove("d-none");
            this.startTimer(el);
        };
    }

    // 3. زر إيقاف التسجيل
    if (el.stopBtn) {
        el.stopBtn.onclick = () => {
            if (this.recorder && this.recorder.state !== "inactive") {
                this.recorder.stop(); // هذا سيستدعي recorder.onstop تلقائياً
            }
        };
    }

    // 4. زر الإغلاق (X)
    if (el.closeCam) {
        el.closeCam.onclick = () => this.closeCamera(el);
    }

    // 5. زر تبديل الكاميرا
    if (el.switchCam) {
        el.switchCam.onclick = async () => {
            this.useFront = !this.useFront;
            this.stopStream(); // إيقاف الحالية
            await this.startStream(el); // تشغيل الجديدة
        };
    }
  },

  async startStream(el) {
      const constraints = {
          video: { facingMode: this.useFront ? "user" : "environment" },
          audio: false
      };
      try {
          this.stream = await navigator.mediaDevices.getUserMedia(constraints);
          el.preview.srcObject = this.stream;
          // عكس الصورة لو الكاميرا أمامية لتكون مثل المرآة
          el.preview.style.transform = this.useFront ? "scaleX(-1)" : "scaleX(1)";
      } catch (err) {
          console.error("Stream Error:", err);
          throw err;
      }
  },

  stopStream() {
      if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop());
          this.stream = null;
      }
  },

  closeCamera(el) {
      this.stopStream();
      if(el.preview) el.preview.srcObject = null;
      if(this.container) this.container.classList.add("d-none");
      this.resetUI(el);
      this.stopTimer(el);
  },

  startTimer(el) {
      if(el.timer) {
          el.timer.classList.remove("d-none");
          el.timer.innerText = "00:00";
          let seconds = 0;
          this.timerInterval = setInterval(() => {
              seconds++;
              const m = Math.floor(seconds / 60).toString().padStart(2, '0');
              const s = (seconds % 60).toString().padStart(2, '0');
              el.timer.innerText = `${m}:${s}`;
          }, 1000);
      }
  },

  stopTimer(el) {
      clearInterval(this.timerInterval);
      if(el.timer) el.timer.classList.add("d-none");
  },

  resetUI(el) {
      if(el.startBtn) el.startBtn.classList.remove("d-none");
      if(el.stopBtn) el.stopBtn.classList.add("d-none");
  },

  async sendVideo(CSRF) {
      try {
          if (!CSRF) {
              console.error("CSRF Token is missing!");
              return "❌ Security Error(CSRF)";
          }

          if (this.chunks.length === 0) return null;
          
          const blob = new Blob(this.chunks, { type: "video/webm" });
          const fd = new FormData();
          fd.append("video", blob, "sign.webm");
          
          // إرسال الطلب للسيرفر
          const res = await fetch("/api/predict-sign/", {
              method: "POST", 
              headers: { "X-CSRFToken": CSRF }, 
              body: fd
          });
          
          if (!res.ok) {
              throw new Error(`Server Error: ${res.status}`);
          }

          const data = await res.json();
          return data.status === "success" ? data.data.sentence : "❌ Not recognized";
          
      } catch (err) {
          console.error("Send Video Error:", err);
          return "❌ Connection error";
      }
  }
};