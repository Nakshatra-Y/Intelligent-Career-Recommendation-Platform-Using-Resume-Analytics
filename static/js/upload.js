document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('resumeFile');
    const fileNameDisplay = document.getElementById('fileName');
    const fileInfo = document.getElementById('fileInfo');
    const removeFileBtn = document.getElementById('removeFile');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loaderOverlay = document.getElementById('loaderOverlay');
    const displayUserName = document.getElementById('displayUserName');

    // Display username from localStorage
    const userName = localStorage.getItem('userName');
    if (userName) {
        displayUserName.textContent = userName;
    }

    let selectedFile = null;

    // Drag and Drop Handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelection(e.target.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        dropZone.classList.remove('hidden');
        analyzeBtn.disabled = true;
    });

    const handleFileSelection = (file) => {
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const extension = file.name.split('.').pop().toLowerCase();

        if (allowedTypes.includes(file.type) || extension === 'pdf' || extension === 'docx') {
            selectedFile = file;
            fileNameDisplay.textContent = file.name;
            fileInfo.classList.remove('hidden');
            dropZone.classList.add('hidden');
            analyzeBtn.disabled = false;
        } else {
            alert('Please upload only .pdf or .docx files');
            fileInput.value = '';
        }
    };

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        loaderOverlay.classList.remove('hidden');

        const formData = new FormData();
        formData.append('resume', selectedFile);

        try {
            // Simulated delay for UI demonstration
            await new Promise(resolve => setTimeout(resolve, 2000));

            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Analysis failed. Please try again later.');
            }

            const data = await response.json();

            // Save response in localStorage
            localStorage.setItem('analysisResult', JSON.stringify(data));

            // Redirect to result page
            window.location.href = '/result';

        } catch (error) {
            console.error('Error:', error);

            // For demo purposes, if backend is not running, we'll save mock data
            console.warn('Backend not reachable. saving mock data for demonstration.');
            const mockData = {
                candidate_name: "John Doe",
                skills: ["JavaScript", "Python", "React", "Node.js", "AI/ML", "SQL", "Cloud Computing"],
                education: "B.S. in Computer Science, University of Technology",
                experience: "3+ years of Software Development experience at Tech Corp.",
                ai_summary: "John is a highly skilled software engineer with a strong background in web development and artificial intelligence. His experience at Tech Corp shows progressive responsibility and technical growth.",
                insights: {
                    strengths: ["Strong full-stack foundation", "Multiple programming languages", "Proven track record in team environments"],
                    weaknesses: ["limited experience with mobile development", "Lack of leadership certification"],
                    missing_skills: ["Docker", "Kubernetes", "AWS Lambda"],
                    improvement_areas: ["Earn a cloud architecture certification", "Contribute more to open-source projects", "Update Portfolio website"]
                }
            };

            localStorage.setItem('analysisResult', JSON.stringify(mockData));
            setTimeout(() => {
                window.location.href = '/result';
            }, 1000);

        } finally {
            // Usually we'd hide the loader if not redirecting, but redirect is expected
            // loaderOverlay.classList.add('hidden');
        }
    });
});
