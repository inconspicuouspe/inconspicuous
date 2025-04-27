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
{% if Settings._CREATE_MEMBERS in session.settings %}
const settingsValues = {
    {% for setting in Settings.__members__.values() %}
    {% if setting in session.settings %}
    setting_{{ setting.name }}: {{ setting.value }},
    {% endfor %}
    {% endfor %}
};
const addUserButton = document.querySelector("#addUserForm");
const settingsDiv = document.querySelector("div.settings-box");
addUserButton.addEventListener("submit", (event) => {
    event.preventDefault();
    const settingsValue = 0;
    for (const child of settingsDiv.children) {
        settingsValue |= settingsValues[child.children[0].name] * child.children[0].checked;
    }
    console.log(settingsValue);
    /*fetch("{{ url_for('add_user') }}" {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify()
    });*/
})
{% endif %}