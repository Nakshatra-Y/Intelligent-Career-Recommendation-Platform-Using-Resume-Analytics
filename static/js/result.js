document.addEventListener('DOMContentLoaded', () => {
    const displayUserName = document.getElementById('displayUserName');
    const candidateName = document.getElementById('candidateName');
    const candidateEducation = document.getElementById('candidateEducation');
    const candidateExperience = document.getElementById('candidateExperience');
    const aiSummary = document.getElementById('aiSummary');
    const skillsContainer = document.getElementById('skillsContainer');
    const resumeScore = document.getElementById('resumeScore');
    const jobRolesList = document.getElementById('jobRolesList');

    // Display username
    const userName = localStorage.getItem('userName');
    if (userName) {
        displayUserName.textContent = userName;
    }

    // Get analysis data
    const rawData = localStorage.getItem('analysisResult');
    if (!rawData) {
        window.location.href = '/upload';
        return;
    }

    const data = JSON.parse(rawData);

    // Populate Data
    candidateName.textContent = data.candidate_name || "N/A";
    candidateEducation.textContent = data.education || "No education info found";
    candidateExperience.textContent = data.experience || "No experience info found";
    aiSummary.textContent = data.ai_summary || "No AI summary generated";

    if (resumeScore) resumeScore.textContent = data.resume_score || "N/A";

    if (jobRolesList) {
        if (data.job_roles && data.job_roles.length > 0) {
            jobRolesList.innerHTML = data.job_roles.map(role => `<li>${role}</li>`).join('');
        } else {
            jobRolesList.innerHTML = '<li style="color: var(--text-muted);">No roles suggested</li>';
        }
    }

    // Dynamic rendering of skills using map()
    if (data.skills && data.skills.length > 0) {
        skillsContainer.innerHTML = data.skills.map(skill => `
            <span class="skill-tag">${skill}</span>
        `).join('');
    } else {
        skillsContainer.innerHTML = '<p style="color: var(--text-muted)">No skills detected</p>';
    }
});
