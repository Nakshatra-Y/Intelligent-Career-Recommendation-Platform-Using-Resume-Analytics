document.addEventListener('DOMContentLoaded', () => {
    const displayUserName = document.getElementById('displayUserName');
    const strengthsList = document.getElementById('strengthsList');
    const weaknessesList = document.getElementById('weaknessesList');
    const missingSkillsList = document.getElementById('missingSkillsList');
    const improvementsList = document.getElementById('improvementsList');

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
    const insights = data.insights || {};

    // Helper function to render list items
    const renderList = (container, items) => {
        if (items && items.length > 0) {
            container.innerHTML = items.map(item => `<li>${item}</li>`).join('');
        } else {
            container.innerHTML = '<li>No specific insights found.</li>';
        }
    };

    // Render each category
    renderList(strengthsList, insights.strengths);
    renderList(weaknessesList, insights.weaknesses);
    renderList(missingSkillsList, insights.missing_skills);
    renderList(improvementsList, insights.improvement_areas);
});
