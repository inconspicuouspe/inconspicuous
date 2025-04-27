const logoutButton = document.querySelector("#logout-button");
logoutButton.addEventListener("click", (event) => {
    fetch("{{ url_for('logout') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
    }).then(()=>{location.reload();});
})
window.lastUsername = null;
{% if Settings._CREATE_MEMBERS in session.settings %}
const settingsValues = { {% for setting in Settings.__members__.values() %}{% if setting in session.settings %}
    setting_{{ setting.name }}: {{ setting.value }},{% endif %}{% endfor %}
};
const addUserButton = document.querySelector("#addUserForm");
const addUserUsernameInput = document.querySelector("#addUserForm #username");
const addUserPgroupInput = document.querySelector("#addUserForm #pgroup");
const addUserSettingsDiv = document.querySelector("#addUserForm div.settings-box");
const addUserMessageBox = document.querySelector("#addUserForm #message");
function addUserSuccess(data) {
    const success = data.success;
    if (success) {
        addUserMessageBox.textContent = lastUsername+" was added. The signup link is: https://"+location.host+"{{ url_for('register') }}?user_slot="+data.{{ consts.FIELD_DATA }};
    }
    else {
        addUserMessageBox.textContent = "That username is already taken."
    }
    addUserMessageBox.style.visibility = "visible";
}
addUserButton.addEventListener("submit", (event) => {
    event.preventDefault();
    window.lastUsername = addUserUsernameInput.value
    let settingsValue = 0;
    for (const child of addUserSettingsDiv.children) {
        settingsValue |= settingsValues[child.children[0].name] * child.children[0].checked;
    }
    console.log(settingsValue);
    fetch("{{ url_for('add_user') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({
            {{ consts.FIELD_USERNAME }}: lastUsername,
            {{ consts.FIELD_PERMISSION_GROUP }}: Number(addUserPgroupInput.value),
            {{ consts.FIELD_SETTINGS }}: settingsValue
        })
    }).then((response) => response.json()).then(addUserSuccess);
})
{% endif %}