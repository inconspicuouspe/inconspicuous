const userListDiv = document.querySelector("#userList");
const userListLineTemplate = document.querySelector("template#user-table-line-template");
const userListButtonTemplate = document.querySelector("template#user-table-option-button-template");

function createUserListLine() {
    return document.importNode(userListLineTemplate.content.querySelector("tr"), true);
}

function createUserListButton() {
    return document.importNode(userListButtonTemplate.content.querySelector("button"), true);
}

function userListSuccess(data){
    const success = data.{{ consts.FIELD_SUCCESS }};
    if (!success) return;
    const userListTable = userListDiv.querySelector("tbody");
    userListDiv.firstChild.remove();
    for (const user of data.{{ consts.FIELD_DATA }}) {
        const username = user.{{ consts.FIELD_USERNAME }};
        const pgroup = user.{{ consts.FIELD_PERMISSION_GROUP }};
        const settings = user.{{ consts.FIELD_SETTINGS }};
        const unfilled = user.{{ consts.FIELD_USER_ID }} === "???";
        const currentLine = createUserListLine();
        currentLine.classList.add("username-"+username);
        currentLine.querySelector(".username-column").textContent = username;
        currentLine.querySelector(".pgroup-column").textContent = pgroup !== -1 ? pgroup : "?";
        currentLine.querySelector(".status-column").textContent = unfilled ? "Eingeladen" : "Mitglied";
        const settingsList = currentLine.querySelector(".settings-column .settings-list");
        if (settings === -1){
            const settingsColumn = currentLine.querySelector(".settings-column");
            settingsColumn.firstElementChild.remove();
            settingsColumn.textContent = "?";
        } else {
            for (const name in settingsValues) {
                if (!name.startsWith("setting__") && name !== "setting_NONE" && (settingsValues[name] & settings) === settingsValues[name]) {
                    const settingElm = document.createElement("li");
                    settingElm.textContent = settingsNames[name];
                    settingsList.appendChild(settingElm);
                }
            }
        }
        if (pgroup !== -1 && pgroup < ownPgroup) {
            {% if Settings._DISABLE_MEMBERS in session.settings %}
            const disableButton = createUserListButton();
            disableButton.textContent = "Entregristrieren";
            disableButton.classList.add("disable-button");
            disableButton.targetUsername = username;
            disableButton.onclick = (event) => {
                if (event.target.textContent === "...") return;
                event.target.textContent = "...";
                fetch("{{ url_for('deactivate_user') }}", {
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
                    },
                    method: "POST",
                    body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: event.target.targetUsername })
                }).then((response) => response.json()).then((data) => {
                    event.target.textContent = "Entregristrieren";
                    if (data.success) {
                        event.target.style.display = "none";
                        const deleteButton = document.querySelector("#userList .username-"+event.target.targetUsername+" .delete-button")
                        if (deleteButton) deleteButton.style.display = "";
                    }
                });
            }
            if (unfilled) {
                disableButton.style.display = "none";
            }
            currentLine.querySelector(".options-column").appendChild(disableButton);
            {% endif %}
            {% if Settings._UNINVITE_MEMBERS in session.settings %}
            const deleteButton = createUserListButton();
            deleteButton.textContent = "Löschen";
            deleteButton.classList.add("delete-button");
            deleteButton.targetUsername = username;
            deleteButton.onclick = (event) => {
                if (event.target.textContent === "...") return;
                event.target.textContent = "...";
                fetch("{{ url_for('remove_user') }}", {
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
                    },
                    method: "POST",
                    body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: event.target.targetUsername })
                }).then((response) => response.json()).then((data) => {
                    event.target.textContent = "Löschen";
                    if (data.success) {
                        event.target.parentNode.parentNode.remove()
                    }
                });
            }
            if (!unfilled) {
                deleteButton.style.display = "none";
            }
            currentLine.querySelector(".options-column").appendChild(deleteButton);
            {% endif %}
        }
        userListTable.appendChild(currentLine);
    }
    userListTable.parentNode.style.display = "";
}

function userListLoad() {
    fetch("{{ url_for('get_user_list') }}")
        .then((response) => response.json()).then(userListSuccess);
}

function userListRefresh() {
    for (const elm of document.querySelectorAll(".user-row")) {
        elm.remove();
    }
    const userListTable = userListDiv.querySelector("tbody");
    userListTable.parentNode.style.display = "none";
    userListDiv.prepend("...");
    userListLoad();
}

