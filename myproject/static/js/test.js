console.log("🔥 TEST JS LOADED");

document.addEventListener("DOMContentLoaded", () => {
  console.log("🔥 DOM READY");

  const sendBtn = document.getElementById("sendBtn");
  console.log("SEND BTN =", sendBtn);

  if (sendBtn) {
    sendBtn.addEventListener("click", () => {
      alert("✅ SEND CLICK WORKS");
    });
  }
});
