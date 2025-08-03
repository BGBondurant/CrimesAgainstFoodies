document.addEventListener('DOMContentLoaded', function() {
    const loginSection = document.getElementById('login-section');
    const suggestionsSection = document.getElementById('suggestions-section');
    const loginButton = document.getElementById('github-login-btn');
    const suggestionsListDiv = document.getElementById('suggestions-list');
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    // const logoImage = document.getElementById('admin-logo-image'); // Not directly used in this script's new logic
    const newSuggestionItemNameInput = document.getElementById('new-suggestion-item-name');
    const addNewSuggestionButton = document.getElementById('add-new-suggestion-btn');

    // Simulate login
    if (loginButton) {
        loginButton.addEventListener('click', function() {
            // In a real app, this would trigger GitHub OAuth flow.
            // For now, we just "log in" and show the suggestions.
            console.log("Simulated GitHub login initiated.");
            if (loginSection) {
                loginSection.classList.add('hidden');
            }
            if (suggestionsSection) {
                suggestionsSection.classList.remove('hidden');
            }
            loadSuggestions();
        });
    }

    // Add New Suggestion Functionality
    if (addNewSuggestionButton && newSuggestionItemNameInput) {
        addNewSuggestionButton.addEventListener('click', function() {
            const itemName = newSuggestionItemNameInput.value.trim();
            if (itemName) {
                const newSuggestion = {
                    id: `new_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`, // Temporary unique ID
                    item: itemName,
                    status: 'Pending', // Default status for new items
                    date: new Date().toISOString()
                };
                addSuggestionToDOM(newSuggestion);
                newSuggestionItemNameInput.value = ''; // Clear the input field
                console.log("Simulated: Added new suggestion to list:", newSuggestion);
                // alert(`"${itemName}" added to the suggestions list (simulated).`); // Alert can be noisy
            } else {
                alert('Please enter a name for the food item suggestion.');
            }
        });
    }
    function loadSuggestions() {
        if (!suggestionsListDiv) return;

        suggestionsListDiv.innerHTML = '<p>Loading suggestions...</p>'; // Show loading message

        fetch('/api/suggestions')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
                }
                return response.json();
            })
            .then(suggestions => {
                displaySuggestions(suggestions);
            })
            .catch(error => {
                console.error('Error loading suggestions:', error);
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

    // Function to add a single new suggestion to the DOM (prepends to list)
    function addSuggestionToDOM(suggestion) {
        if (!suggestionsListDiv) return;

        // If "No pending suggestions" or error/loading message is present, remove it
        const existingMessageP = suggestionsListDiv.querySelector('p');
        if (existingMessageP && (
            existingMessageP.textContent === 'No pending suggestions found.' ||
            existingMessageP.textContent === 'Loading suggestions...' ||
            existingMessageP.classList.contains('error')
        )) {
            suggestionsListDiv.innerHTML = '';
        }

        const itemDiv = createSuggestionItemElement(suggestion);
        suggestionsListDiv.prepend(itemDiv); // Add to the top for visibility
    }

    // Helper to escape HTML to prevent XSS if data isn't trusted
    function escapeHTML(str) {
        if (typeof str !== 'string') return str; // Return non-strings as is
        return str.replace(/[&<>"']/g, function (match) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[match];
        });
    }

    function renderSuggestionContent(contentElement, suggestion) {
        contentElement.innerHTML = `<strong>Item:</strong> ${escapeHTML(suggestion.item) || 'N/A'}<br>
                                    <strong>Status:</strong> ${escapeHTML(suggestion.status) || 'N/A'}<br>
                                    <strong>Date:</strong> ${suggestion.date ? new Date(suggestion.date).toLocaleString() : 'N/A'}`;
    }

    function createSuggestionItemElement(suggestion) {
        const itemDiv = document.createElement('div');
        itemDiv.classList.add('suggestion-item');
        itemDiv.setAttribute('data-suggestion-id', suggestion.id); // Store ID for reference

        const contentP = document.createElement('p');
        contentP.classList.add('suggestion-content-display');
        renderSuggestionContent(contentP, suggestion);
        itemDiv.appendChild(contentP);

        // Container for edit form inputs (initially hidden)
        const editFormInputsDiv = document.createElement('div');
        editFormInputsDiv.classList.add('edit-form-inputs', 'hidden');
        itemDiv.appendChild(editFormInputsDiv);

        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('suggestion-item-actions');

        const approveButton = document.createElement('button');
        approveButton.textContent = 'Approve';
        approveButton.classList.add('approve-btn');
        approveButton.addEventListener('click', () => {
            fetch('/api/suggestions/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: suggestion.id, item: suggestion.item })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                itemDiv.remove();
            })
            .catch(error => {
                console.error('Error approving suggestion:', error);
                alert('Could not approve suggestion.');
            });
        });

        const rejectButton = document.createElement('button');
        rejectButton.textContent = 'Reject';
        rejectButton.classList.add('reject-btn');
        rejectButton.addEventListener('click', () => {
            fetch('/api/suggestions/reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: suggestion.id })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                itemDiv.remove();
            })
            .catch(error => {
                console.error('Error rejecting suggestion:', error);
                alert('Could not reject suggestion.');
            });
        });

        actionsDiv.appendChild(approveButton);
        actionsDiv.appendChild(rejectButton);
        itemDiv.appendChild(actionsDiv);

        return itemDiv;
    }

    function toggleEditMode(itemDiv, suggestion, isEditing) {
        const contentDisplay = itemDiv.querySelector('.suggestion-content-display');
        const editFormInputsDiv = itemDiv.querySelector('.edit-form-inputs');
        const actionsDiv = itemDiv.querySelector('.suggestion-item-actions'); // The div containing Approve/Reject/Edit

        if (isEditing) {
            contentDisplay.classList.add('hidden');
            actionsDiv.classList.add('hidden'); // Hide Approve/Reject/Edit buttons

            // Create and append edit form elements
            editFormInputsDiv.innerHTML = `
                <label for="edit-item-${suggestion.id}">Item Name:</label>
                <input type="text" id="edit-item-${suggestion.id}" value="${escapeHTML(suggestion.item || '')}">
                <label for="edit-status-${suggestion.id}">Status:</label>
                <input type="text" id="edit-status-${suggestion.id}" value="${escapeHTML(suggestion.status || '')}">
                <button class="save-edit-btn">Save</button>
                <button class="cancel-edit-btn">Cancel</button>
            `;
            editFormInputsDiv.classList.remove('hidden');

            editFormInputsDiv.querySelector('.save-edit-btn').addEventListener('click', () => {
                const updatedItem = itemDiv.querySelector(`#edit-item-${suggestion.id}`).value.trim();
                const updatedStatus = itemDiv.querySelector(`#edit-status-${suggestion.id}`).value.trim();

                if (updatedItem) {
                    suggestion.item = updatedItem; // Update the in-memory suggestion object
                    suggestion.status = updatedStatus;
                    renderSuggestionContent(contentDisplay, suggestion); // Update the display paragraph
                    console.log(`Simulated: Saved changes for suggestion ID ${suggestion.id}`, suggestion);
                    // alert(`Changes to "${suggestion.item}" saved (simulated).`); // Can be noisy
                    toggleEditMode(itemDiv, suggestion, false); // Exit edit mode
                } else {
                    alert('Item name cannot be empty.');
                }
            });

            editFormInputsDiv.querySelector('.cancel-edit-btn').addEventListener('click', () => {
                toggleEditMode(itemDiv, suggestion, false); // Exit edit mode, discard changes
            });
        } else { // Exiting edit mode
            contentDisplay.classList.remove('hidden');
            actionsDiv.classList.remove('hidden'); // Show Approve/Reject/Edit buttons
            editFormInputsDiv.classList.add('hidden');
            editFormInputsDiv.innerHTML = ''; // Clear the edit form
        }
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

    // Ensure login button exists before trying to add event listener
    // (already handled by `if (loginButton)` check above)
});