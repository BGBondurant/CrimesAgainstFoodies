document.addEventListener('DOMContentLoaded', function() {
    const loginSection = document.getElementById('login-section');
    const suggestionsSection = document.getElementById('suggestions-section');
    const loginButton = document.getElementById('github-login-btn');
    const suggestionsListDiv = document.getElementById('suggestions-list');
    const newSuggestionItemNameInput = document.getElementById('new-suggestion-item-name');
    const newSuggestionTypeSelect = document.getElementById('new-suggestion-type-select');
    const addNewSuggestionButton = document.getElementById('add-new-suggestion-btn');

    if (loginButton) {
        loginButton.addEventListener('click', function() {
            console.log("Simulated GitHub login initiated.");
            if (loginSection) loginSection.classList.add('hidden');
            if (suggestionsSection) suggestionsSection.classList.remove('hidden');
            loadSuggestions();
        });
    }

    if (addNewSuggestionButton && newSuggestionItemNameInput && newSuggestionTypeSelect) {
        addNewSuggestionButton.addEventListener('click', function() {
            const itemName = newSuggestionItemNameInput.value.trim();
            const itemType = newSuggestionTypeSelect.value;
            if (itemName) {
                const newSuggestionData = {
                    item: itemName,
                    status: 'pending',
                    date: new Date().toISOString(),
                    type: itemType
                };
                fetch('/api/suggestions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSuggestionData)
                })
                .then(response => {
                    if (!response.ok) throw new Error('Failed to add suggestion.');
                    return response.json();
                })
                .then(newSuggestion => {
                    addSuggestionToDOM(newSuggestion);
                    newSuggestionItemNameInput.value = '';
                    alert(`Suggestion "${itemName}" added successfully.`);
                })
                .catch(error => {
                    console.error('Error adding suggestion:', error);
                    alert('Could not add suggestion.');
                });
            } else {
                alert('Please enter a name for the food item suggestion.');
            }
        });
    }

    function loadSuggestions() {
        if (!suggestionsListDiv) return;
        suggestionsListDiv.innerHTML = '<p>Loading suggestions...</p>';
        fetch('/api/suggestions')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(displaySuggestions)
            .catch(error => {
                console.error('Error loading suggestions:', error);
                if (suggestionsListDiv) suggestionsListDiv.innerHTML = `<p class="error">Could not load suggestions. Error: ${error.message}</p>`;
            });
    }

    function displaySuggestions(suggestions) {
        if (!suggestionsListDiv) return;
        suggestionsListDiv.innerHTML = '';
        if (!suggestions || suggestions.length === 0) {
            suggestionsListDiv.innerHTML = '<p>No pending suggestions found.</p>';
            return;
        }
        suggestions.forEach(suggestion => {
            const itemDiv = createSuggestionItemElement(suggestion);
            suggestionsListDiv.appendChild(itemDiv);
        });
    }

    function addSuggestionToDOM(suggestion) {
        if (!suggestionsListDiv) return;
        const existingMessageP = suggestionsListDiv.querySelector('p');
        if (existingMessageP) existingMessageP.remove();
        const itemDiv = createSuggestionItemElement(suggestion);
        suggestionsListDiv.prepend(itemDiv);
    }

    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, match => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[match]));
    }

    function renderSuggestionContent(contentElement, suggestion) {
        const itemTextId = `item-text-${suggestion.id}`;
        contentElement.innerHTML = `<strong>Item:</strong> <span id="${itemTextId}" class="suggestion-item-text">${escapeHTML(suggestion.item)}</span><br>
                                    <strong>Status:</strong> ${escapeHTML(suggestion.status)}<br>
                                    <strong>Type:</strong> ${escapeHTML(suggestion.type)}<br>
                                    <strong>Date:</strong> ${new Date(suggestion.date).toLocaleString()}`;
    }

    function createSuggestionItemElement(suggestion) {
        const itemDiv = document.createElement('div');
        itemDiv.classList.add('suggestion-item');
        itemDiv.setAttribute('data-suggestion-id', suggestion.id);

        const duplicateIndicator = document.createElement('div');
        duplicateIndicator.classList.add('duplicate-indicator');
        itemDiv.appendChild(duplicateIndicator);

        fetch('/api/suggestions/check_duplicates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: suggestion.item })
        })
        .then(response => response.json())
        .then(data => {
            if (data.duplicates.length > 0) {
                duplicateIndicator.textContent = '❌';
                const tooltipText = data.duplicates.map(d => `${d.word} (in ${d.list})`).join(', ');
                duplicateIndicator.title = `Duplicate words found: ${tooltipText}`;
            } else {
                duplicateIndicator.textContent = '✔️';
                duplicateIndicator.title = 'No duplicate words found.';
            }
        });

        const contentP = document.createElement('p');
        contentP.classList.add('suggestion-content-display');
        renderSuggestionContent(contentP, suggestion);
        itemDiv.appendChild(contentP);

        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('suggestion-item-actions');

        const approveButton = document.createElement('button');
        approveButton.textContent = 'Approve';
        approveButton.classList.add('approve-btn');
        approveButton.onclick = () => {
            const type = prompt("Approve as 'foods' or 'preparations'?").toLowerCase();
            if (type === 'foods' || type === 'preparations') {
                if (confirm(`Are you sure you want to approve "${suggestion.item}" as ${type}?`)) {
                    fetch('/api/suggestions/approve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: suggestion.id, item: suggestion.item, type: type })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        itemDiv.remove();
                    })
                    .catch(error => alert('Could not approve suggestion.'));
                }
            } else {
                alert("Invalid type. Please enter 'foods' or 'preparations'.");
            }
        };

        const rejectButton = document.createElement('button');
        rejectButton.textContent = 'Reject';
        rejectButton.classList.add('reject-btn');
        rejectButton.onclick = () => {
            if (confirm(`Are you sure you want to reject "${suggestion.item}"?`)) {
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
                .catch(error => alert('Could not reject suggestion.'));
            }
        };

        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.classList.add('edit-btn');
        editButton.onclick = () => setEditMode(itemDiv, suggestion, true);

        const saveButton = document.createElement('button');
        saveButton.textContent = 'Save';
        saveButton.classList.add('save-edit-btn', 'hidden');

        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancel';
        cancelButton.classList.add('cancel-edit-btn', 'hidden');

        actionsDiv.append(approveButton, editButton, rejectButton, saveButton, cancelButton);
        itemDiv.appendChild(actionsDiv);

        return itemDiv;
    }

    function setEditMode(itemDiv, suggestion, isEditing) {
        const itemTextElement = itemDiv.querySelector(`#item-text-${suggestion.id}`);
        const actions = itemDiv.querySelector('.suggestion-item-actions');
        const normalButtons = [actions.querySelector('.approve-btn'), actions.querySelector('.reject-btn'), actions.querySelector('.edit-btn')];
        const editButtons = [actions.querySelector('.save-edit-btn'), actions.querySelector('.cancel-edit-btn')];

        itemTextElement.contentEditable = isEditing;
        itemTextElement.classList.toggle('editing', isEditing);
        normalButtons.forEach(btn => btn.classList.toggle('hidden', isEditing));
        editButtons.forEach(btn => btn.classList.toggle('hidden', !isEditing));

        if (isEditing) {
            itemTextElement.focus();
            const originalText = suggestion.item;

            actions.querySelector('.save-edit-btn').onclick = () => {
                const updatedItemText = itemTextElement.innerText.trim();
                if (!updatedItemText) {
                    alert('Suggestion item cannot be empty.');
                    itemTextElement.innerText = originalText;
                    return;
                }
                fetch('/api/suggestions/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: suggestion.id, item: updatedItemText, status: suggestion.status })
                })
                .then(response => {
                    if (!response.ok) throw new Error('Update failed');
                    suggestion.item = updatedItemText; // Update local data on success
                    alert('Suggestion updated successfully!');
                })
                .catch(error => {
                    itemTextElement.innerText = originalText; // Revert on failure
                    alert('Could not update suggestion.');
                })
                .finally(() => setEditMode(itemDiv, suggestion, false));
            };

            actions.querySelector('.cancel-edit-btn').onclick = () => {
                itemTextElement.innerText = originalText;
                setEditMode(itemDiv, suggestion, false);
            };
        }
    }
});