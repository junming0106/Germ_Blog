document.addEventListener("DOMContentLoaded", () => {
  console.log("DOMContentLoaded");
  const password = document.querySelector("#password");
  const confirm_password = document.querySelector("#confirm_password");
  if (password.value !== confirm_password.value) {
    alert("密碼不一致");
  }
  if (password.length < 8) {
    alert("密碼長度至少8個字");
  }
});
