import os
import cv2
import torch
import json
import numpy as np

from torchvision.transforms import Compose, Lambda
from pytorchvideo.transforms import ShortSideScale, Normalize
from pytorchvideo.models.hub import slowfast_r50


# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "SignTalk_Best_Model.pth")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "WLASL_150.json")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

NUM_FRAMES = 32
SIDE_SIZE = 256
MEAN = [0.45, 0.45, 0.45]
STD = [0.225, 0.225, 0.225]


# ================= PACK SLOWFAST PATHWAY =================
class PackPathway(torch.nn.Module):
    """
    Split video tensor into SlowFast pathways
    Input:  [C, T, H, W]
    Output: [slow_pathway, fast_pathway]
    """
    def forward(self, frames: torch.Tensor):
        fast_pathway = frames                          # [3, 32, H, W]
        slow_pathway = frames[:, ::4, :, :]            # [3, 8, H, W]
        return [slow_pathway, fast_pathway]


# ================= PREDICTOR =================
class SignLanguagePredictor:
    def __init__(self):
        print("🚀 Loading AI Sign Model...")
        self.model = None
        self.class_names = {}
        self.transform = None
        self.ready = False
        self._load_resources()

    # ---------------- LOAD MODEL ----------------
    def _load_resources(self):
        try:
            # ===== load class names =====
            with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                self.class_names = {int(k): v for k, v in data.items()}
            elif isinstance(data, list):
                self.class_names = {i: v for i, v in enumerate(data)}
            else:
                raise ValueError("Invalid class names format")

            # بيعد الكلمات أوتوماتيك (150 كلمة) عشان الموديل يتبني صح
            num_classes = len(self.class_names)

            # ===== load SlowFast backbone =====
            print("⏳ Building SlowFast backbone...")
            self.model = slowfast_r50(pretrained=False)

            # ===== replace classification head =====
            in_features = self.model.blocks[-1].proj.in_features
            
            # هنا بيحط الـ 150 كلمة مكان الـ Linear القديم
            self.model.blocks[-1].proj = torch.nn.Linear(
                in_features, num_classes
            )

            # ===== load trained weights =====
            state = torch.load(MODEL_PATH, map_location=DEVICE)
            self.model.load_state_dict(state, strict=True)

            self.model.to(DEVICE)
            self.model.eval()

            # ===== CORRECT VIDEO TRANSFORMS ORDER =====
            self.transform = Compose([
                Lambda(lambda x: x / 255.0),        # [C, T, H, W] → normalize range
                ShortSideScale(SIDE_SIZE),          # resize frames
                Normalize(mean=MEAN, std=STD),      # channel-wise normalize
                PackPathway(),                      # split slow / fast (LAST)
            ])

            self.ready = True
            print(f"✅ Model Loaded Successfully with {num_classes} classes!")

        except Exception as e:
            print("❌ Error loading model:", e)
            self.ready = False

    # ---------------- PREDICT ----------------
    def predict_video(self, video_path, threshold=0.30):
        if not self.ready:
            return {"status": "error", "message": "Model not ready"}

        cap = cv2.VideoCapture(video_path)
        frames = []

        # ===== read video =====
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)

        cap.release()

        # ===== if video too short =====
        if len(frames) < NUM_FRAMES:
            return {"status": "success", "sentence": "", "words": []}

        raw_words = []

        # ===== sliding window over video =====
        for start in range(0, len(frames) - NUM_FRAMES + 1, 10):
            clip = np.array(frames[start:start + NUM_FRAMES])   # [T, H, W, C]

            # to tensor: [C, T, H, W]
            tensor = torch.from_numpy(clip).permute(3, 0, 1, 2).float()

            # apply video transforms
            inputs = self.transform(tensor)

            # add batch dimension
            inputs = [x.unsqueeze(0).to(DEVICE) for x in inputs]

            # ===== inference =====
            with torch.no_grad():
                logits = self.model(inputs)
                probs = torch.softmax(logits, dim=1)
                prob, idx = torch.max(probs, dim=1)

                if prob.item() >= threshold:
                    raw_words.append(self.class_names[idx.item()])

        if not raw_words:
            return {"status": "success", "sentence": "", "words": []}

        # ===== temporal smoothing =====
        words = [raw_words[0]]
        for w in raw_words[1:]:
            if w != words[-1]:
                words.append(w)

        return {
            "status": "success",
            "sentence": " ".join(words),
            "words": words
        }


# ================= GLOBAL INSTANCE =================
predictor = SignLanguagePredictor()