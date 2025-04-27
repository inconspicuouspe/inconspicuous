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
    setting_{{ setting.name }}: {{ setting.value }},
    {% endfor %}
};
const addUserButton = document.querySelector("#addUserForm");
addUserButton.addEventListener("submit", (event) => {
    fetch("{{ url_for('add_user') }}");
})
{% endif %}