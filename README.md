# 🎤 AI Interview Preparation System

A comprehensive interview preparation platform featuring a 3D AI interviewer with realistic animations, voice analysis, and personalized feedback.

## ✨ Features

- **3D AI Interviewer**: Realistic avatar with sitting and talking animations
- **Resume Upload & Analysis**: Parse PDF resumes for personalized questions
- **Voice Recording**: Record and analyze interview answers
- **Real-time Feedback**: Get instant scoring and improvement suggestions
- **Progress Tracking**: Monitor your interview performance over time
- **Multiple Roles**: Support for Data Science, ML Engineering, Development, and more

## 📁 Project Structure

```
ai-interview-prep/
├── app.py                    # Main Streamlit application
├── components/
│   └── avatar.html          # 3D avatar interface
├── animations/
│   ├── Sitting.glb          # Sitting idle animation
│   └── Talking.glb          # Talking animation
├── character.glb            # Base character model
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Organize Your Files

Make sure your file structure looks like this:

```
your-project/
├── app.py
├── components/
│   └── avatar.html          ← Put the avatar.html here
├── animations/
│   ├── Sitting.glb          ← Your sitting animation
│   └── Talking.glb          ← Your talking animation
├── character.glb            ← Your character file
└── requirements.txt
```

### Step 3: Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📥 Getting Animation Files

You currently have:
- ✅ `character.glb` - Base character
- ✅ `animations/Sitting.glb` - Sitting animation

You need:
- ⏳ `animations/Talking.glb` - Download from Mixamo

### How to Download Talking Animation:

1. Go to [Mixamo](https://www.mixamo.com/)
2. Select your character
3. Search for "Talking" animation
4. Download settings:
   - Format: **FBX for Unity**
   - Skin: **WITH Skin** ✅
   - Frame Rate: 30
5. Convert FBX to GLB using [anyconv.com/fbx-to-glb-converter](https://anyconv.com/fbx-to-glb-converter/)
6. Save as `animations/Talking.glb`

## 🎯 Usage

### 1. Home Page
- View features and progress statistics
- Quick access to get started

### 2. Upload Resume
- Upload your PDF resume
- Generate personalized interview questions

### 3. Start Interview
- See the 3D AI interviewer
- Switch between sitting (idle) and talking modes
- Answer questions via voice or text
- Get real-time feedback

### 4. View Results
- Review your performance
- Download detailed reports
- Track improvement over time

## 🛠️ Technology Stack

- **Frontend**: Streamlit, HTML/CSS/JavaScript
- **3D Graphics**: Three.js
- **3D Models**: GLB format (from Mixamo)
- **Backend**: Python 3.10+
- **File Processing**: PyPDF2 (coming soon)
- **Voice**: Whisper API (coming soon)

## 🚧 Upcoming Features

- [ ] Resume parsing with PyPDF2
- [ ] Question generation using LLM
- [ ] Voice recording with Whisper
- [ ] Answer scoring system
- [ ] SQLite database for progress tracking
- [ ] PDF report generation

## 📝 Current Status

### ✅ Completed
- Professional 3D avatar interface
- Sitting and talking animations
- Interview office environment
- Streamlit integration
- Navigation system
- Question database

### 🔄 In Progress
- Resume parsing
- Question generation
- Voice recording

## 🐛 Troubleshooting

### Avatar not loading?
1. Check that `components/avatar.html` exists
2. Verify `character.glb` is in the root directory
3. Check browser console (F12) for errors

### Animations not working?
1. Ensure files are named exactly: `Sitting.glb` and `Talking.glb`
2. Verify files are in `animations/` folder
3. Check they were downloaded WITH skin from Mixamo

### Streamlit errors?
```bash
pip install --upgrade streamlit
streamlit run app.py
```

## 📊 Project Info

- **Type**: BCA 3rd Year Project
- **Domain**: AI Interview Preparation
- **Tech Stack**: Python, Streamlit, Three.js, Mixamo
- **Status**: Active Development

## 🤝 Contributing

This is a student project. Suggestions welcome!

## 📄 License

Educational project - Free to use for learning purposes

## 📧 Contact

- GitHub: [Your Username]
- LinkedIn: [Your Profile]

---

Built with ❤️ for interview preparation
