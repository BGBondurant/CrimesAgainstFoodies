document.addEventListener('DOMContentLoaded', function() {
    const suggestionsSection = document.getElementById('suggestions-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const suggestionsListDiv = document.getElementById('suggestions-list');
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    const newSuggestionItemNameInput = document.getElementById('new-suggestion-item-name');
    const addNewSuggestionButton = document.getElementById('add-new-suggestion-btn');

    // Load dashboard and suggestions on page load
    dashboardSection.classList.remove('hidden');
    suggestionsSection.classList.remove('hidden');
    loadDashboardStats();
    loadSuggestions();

    function loadDashboardStats() {
        const statsDiv = document.getElementById('dashboard-stats');
        if (!statsDiv) return;
        statsDiv.innerHTML = '<p>Loading stats...</p>';

        fetch('/api/admin/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(stats => {
                statsDiv.innerHTML = `
                    <p><strong>Pending Suggestions:</strong> ${stats.pending_suggestions}</p>
                    <p><strong>Total Food Items:</strong> ${stats.total_foods}</p>
                    <p><strong>Total Preparation Items:</strong> ${stats.total_preparations}</p>
                `;
            })
            .catch(error => {
                console.error('Error loading dashboard stats:', error);
                statsDiv.innerHTML = `<p class="error">Could not load stats. Error: ${error.message}</p>`;
            });
    }

    // Add New Suggestion Functionality
    if (addNewSuggestionButton && newSuggestionItemNameInput) {
        addNewSuggestionButton.addEventListener('click', function() {
            const itemName = newSuggestionItemNameInput.value.trim();
            const selectedTypeElement = document.querySelector('input[name="admin-suggestion-type"]:checked');

            if (!itemName) {
                alert('Please enter a name for the food item suggestion.');
                newSuggestionItemNameInput.focus();
                return;
            }

            if (!selectedTypeElement) {
                alert('Please select a type for the suggestion.');
                return;
            }

            const selectedType = selectedTypeElement.value;

            const newSuggestion = {
                item: itemName,
                type: selectedType
            };

            fetch('/api/suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newSuggestion),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                alert(`Suggestion "${itemName}" of type "${selectedType}" added to the pending list.`);
                loadSuggestions(); // Refresh the list
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('There was an issue adding the suggestion. Please try again later.');
            });

            // Clear input and reset radio to default
            newSuggestionItemNameInput.value = '';
            const defaultRadio = document.getElementById('admin-type-both');
            if (defaultRadio) {
                defaultRadio.checked = true;
            }
        });
    }
    function loadSuggestions() {
        if (!suggestionsListDiv) return;
        suggestionsListDiv.innerHTML = '<p>Loading suggestions...</p>';

        fetch('/api/admin/suggestions')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(suggestions => {
                displaySuggestions(suggestions);
            })
            .catch(error => {
                console.error('Error loading suggestions from backend:', error);
                if (suggestionsListDiv) {
                    suggestionsListDiv.innerHTML = `<p class="error">Could not load suggestions. Error: ${error.message}</p>`;
                }
            });
    }

    function displaySuggestions(suggestions) {
        if (!suggestionsListDiv) return;

        if (!suggestions || suggestions.length === 0) {
            suggestionsListDiv.innerHTML = '<p>No pending suggestions found.</p>';
            return;
        }

        suggestionsListDiv.innerHTML = ''; // Clear loading/error message

        suggestions.forEach(suggestion => {
            const itemDiv = createSuggestionItemElement(suggestion);
            suggestionsListDiv.appendChild(itemDiv);
        });
    }

    // Helper to escape HTML to prevent XSS if data isn't trusted
    function escapeHTML(str) {
        if (typeof str !== 'string') return str; // Return non-strings as is
        return str.replace(/[&<>"']/g, function (match) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[match];
        });
    }

    function renderSuggestionContent(contentElement, suggestion) {
        // Ensure suggestion.type is displayed. Default to 'N/A' if not present.
        const typeDisplay = escapeHTML(suggestion.type || 'N/A');
        const usernameDisplay = escapeHTML(suggestion.username || 'Anonymous');
        contentElement.innerHTML = `<strong>Item:</strong> ${escapeHTML(suggestion.item) || 'N/A'}<br>
                                    <strong>Type:</strong> ${typeDisplay}<br>
                                    <strong>Status:</strong> ${escapeHTML(suggestion.status) || 'N/A'}<br>
                                    <strong>Date:</strong> ${suggestion.submission_date ? new Date(suggestion.submission_date).toLocaleString() : 'N/A'}<br>
                                    <strong>IP Address:</strong> ${escapeHTML(suggestion.ip_address) || 'N/A'}<br>
                                    <strong>Username:</strong> ${usernameDisplay}<br>
                                    <strong>Request Count:</strong> ${suggestion.user_request_count || 'N/A'}`;
    }

    function createSuggestionItemElement(suggestion) {
        const itemDiv = document.createElement('div');
        itemDiv.classList.add('suggestion-item');
        itemDiv.setAttribute('data-suggestion-id', suggestion.id); // Store ID for reference

        const contentP = document.createElement('p');
        contentP.classList.add('suggestion-content-display');
        renderSuggestionContent(contentP, suggestion); // renderSuggestionContent now includes the type

        itemDiv.appendChild(contentP);

        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('suggestion-item-actions');

        const approveButton = document.createElement('button');
        approveButton.textContent = 'Approve';
        approveButton.classList.add('approve-btn');
        approveButton.addEventListener('click', () => {
            fetch(`/api/admin/approve/${suggestion.id}`, {
                method: 'POST',
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                alert(`"${suggestion.item}" approved and removed from pending list.`);
                loadSuggestions();
                loadDashboardStats();
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('There was an issue approving the suggestion. Please try again later.');
            });
        });

        const rejectButton = document.createElement('button');
        rejectButton.textContent = 'Reject';
        rejectButton.classList.add('reject-btn');
        rejectButton.addEventListener('click', () => {
            fetch(`/api/admin/reject/${suggestion.id}`, {
                method: 'DELETE',
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                alert(`"${suggestion.item}" rejected.`);
                loadSuggestions();
                loadDashboardStats();
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('There was an issue rejecting the suggestion. Please try again later.');
            });
        });

        actionsDiv.appendChild(approveButton);
        actionsDiv.appendChild(rejectButton);
        itemDiv.appendChild(actionsDiv);

        return itemDiv;
    }

    // Theme Toggle Functionality
    function setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('adminTheme', theme);
        if (themeToggleButton) {
            themeToggleButton.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme') || 
                                 (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    // Apply saved theme or system preference on load
    const savedTheme = localStorage.getItem('adminTheme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        setTheme(savedTheme);
    } else if (systemPrefersDark) {
        setTheme('dark');
    } else {
        setTheme('light'); // Default to light if no preference
    }
});
