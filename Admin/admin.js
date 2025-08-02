document.addEventListener('DOMContentLoaded', function() {
    const loginSection = document.getElementById('login-section');
    const suggestionsSection = document.getElementById('suggestions-section');
    const loginButton = document.getElementById('github-login-btn');
    const suggestionsListDiv = document.getElementById('suggestions-list');
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
        // Add a span with a unique ID for the item text to make it targetable for editing
        const itemTextId = `item-text-${suggestion.id}`;
        contentElement.innerHTML = `<strong>Item:</strong> <span id="${itemTextId}" class="suggestion-item-text">${escapeHTML(suggestion.item) || 'N/A'}</span><br>
                                    <strong>Status:</strong> ${escapeHTML(suggestion.status) || 'N/A'}<br>
                                    <strong>Date:</strong> ${suggestion.date ? new Date(suggestion.date).toLocaleString() : 'N/A'}`;
    }

    function createSuggestionItemElement(suggestion) {
        const itemDiv = document.createElement('div');
        itemDiv.classList.add('suggestion-item');
        itemDiv.setAttribute('data-suggestion-id', suggestion.id);

        const contentP = document.createElement('p');
        contentP.classList.add('suggestion-content-display');
        renderSuggestionContent(contentP, suggestion);
        itemDiv.appendChild(contentP);

        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('suggestion-item-actions');

        // Normal state buttons
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

        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.classList.add('edit-btn');
        editButton.addEventListener('click', () => {
            setEditMode(itemDiv, suggestion, true);
        });

        // Edit state buttons (initially hidden)
        const saveButton = document.createElement('button');
        saveButton.textContent = 'Save';
        saveButton.classList.add('save-edit-btn', 'hidden');

        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancel';
        cancelButton.classList.add('cancel-edit-btn', 'hidden');

        actionsDiv.appendChild(approveButton);
        actionsDiv.appendChild(editButton);
        actionsDiv.appendChild(rejectButton);
        actionsDiv.appendChild(saveButton);
        actionsDiv.appendChild(cancelButton);
        itemDiv.appendChild(actionsDiv);

        return itemDiv;
    }

    function setEditMode(itemDiv, suggestion, isEditing) {
        const itemTextElement = itemDiv.querySelector(`#item-text-${suggestion.id}`);

        // Get all buttons in the current item's action div
        const approveButton = itemDiv.querySelector('.approve-btn');
        const rejectButton = itemDiv.querySelector('.reject-btn');
        const editButton = itemDiv.querySelector('.edit-btn');
        const saveButton = itemDiv.querySelector('.save-edit-btn');
        const cancelButton = itemDiv.querySelector('.cancel-edit-btn');

        if (isEditing) {
            itemTextElement.setAttribute('contenteditable', 'true');
            itemTextElement.classList.add('editing'); // Add class for styling
            itemTextElement.focus();

            // Hide normal state buttons, show edit state buttons
            approveButton.classList.add('hidden');
            rejectButton.classList.add('hidden');
            editButton.classList.add('hidden');
            saveButton.classList.remove('hidden');
            cancelButton.classList.remove('hidden');

            saveButton.onclick = () => {
                const updatedItemText = itemTextElement.innerText.trim();
                if (!updatedItemText) {
                    alert('Suggestion item cannot be empty.');
                    itemTextElement.innerText = suggestion.item; // Revert to original
                    return;
                }

                // optimistic update in the UI
                const originalItemText = suggestion.item;
                suggestion.item = updatedItemText;

                const updatedData = {
                    id: suggestion.id,
                    item: updatedItemText,
                    status: suggestion.status // Status is not editable in this UI
                };

                fetch('/api/suggestions/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                })
                .then(response => {
                    if (!response.ok) {
                        // If backend fails, revert the optimistic update
                        suggestion.item = originalItemText;
                        itemTextElement.innerText = originalItemText;
                        return response.json().then(err => { throw new Error(err.error || 'Server error') });
                    }
                    return response.json();
                })
                .then(() => {
                    alert('Suggestion updated successfully!');
                })
                .catch(error => {
                    console.error('Error updating suggestion:', error);
                    alert(`Could not update suggestion: ${error.message}`);
                });

                setEditMode(itemDiv, suggestion, false);
            };

            cancelButton.onclick = () => {
                itemTextElement.innerText = suggestion.item; // Revert to original text
                setEditMode(itemDiv, suggestion, false);
            };

        } else { // Exiting edit mode
            itemTextElement.setAttribute('contenteditable', 'false');
            itemTextElement.classList.remove('editing');

            // Show normal state buttons, hide edit state buttons
            approveButton.classList.remove('hidden');
            rejectButton.classList.remove('hidden');
            editButton.classList.remove('hidden');
            saveButton.classList.add('hidden');
            cancelButton.classList.add('hidden');
        }
    }

    // Ensure login button exists before trying to add event listener
    // (already handled by `if (loginButton)` check above)
});