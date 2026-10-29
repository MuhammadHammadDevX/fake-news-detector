# ============================================
# Factify - Training Script
# Yeh script AI model ko train karne ke liye hai.
# Pehle backend/dataset/ folder mein Fake.csv aur True.csv file dalein.
# Phir ye script run karein: python train.py
# ============================================

from model import FactifyModel

if __name__ == '__main__':
    # Console pe heading print karo
    print('=' * 50)
    print('  Factify - Model Training')
    print('=' * 50)
    print()
    print('📂 Make sure Fake.csv and True.csv are in backend/dataset/')
    print()

    # 1. Detector class ka object banao.
    detector = FactifyModel()

    # 2. Training process start karo.
    # Ye function model.py mein defined hai.
    success = detector.train()

    # 3. Result check karo ke training kamyab rahi ya nahi.
    if success:
        print()
        print('✅ Training complete! Model saved.')
        print('🚀 Now run: python app.py')
    else:
        print()
        print('⚠️ Training skipped. Server will use rule-based analysis.')
        print('📥 Download dataset from: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset')
        print('📂 Place Fake.csv and True.csv in backend/dataset/ folder')
        print('🔄 Then run this script again.')
        print()
        print('🚀 You can still run: python app.py (rule-based mode)')

