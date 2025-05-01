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
        const currentLine = createUserListLine();
        currentLine.querySelector(".username-column").textContent = username;
        currentLine.querySelector(".pgroup-column").textContent = pgroup ? pgroup !== -1 : "?";
        const settingsList = currentLine.querySelector(".settings-column .settings-list")
        if (settings === -1){
            const settingElm = document.createElement("li");
            settingElm.textContent = "?";
            settingsList.appendChild(settingElm);
        } else {
            for (const name in settingsValues) {
                if (!name.startsWith("setting__") && name !== "setting_NONE" && (settingsValues[name] & settings) === settingsValues[name]) {
                    console.log(name, username);
                    const settingElm = document.createElement("li");
                    settingElm.textContent = settingsNames[name];
                    settingsList.appendChild(settingElm);
                }
            }
        }
        if (pgroup < ownPgroup) {
            const optionButton = createUserListButton();
            optionButton.textContent = "Option";
            currentLine.querySelector(".options-column").appendChild(optionButton);
        }
        userListTable.appendChild(currentLine);
    }
    userListTable.style.display = "";
}

function userListLoad() {
    fetch("{{ url_for('get_user_list') }}")
        .then((response) => response.json()).then(userListSuccess);
}

