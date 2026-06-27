document.addEventListener("DOMContentLoaded", function () {

    // =============================
    // Live Doctor Search
    // =============================

    const doctorSearch = document.getElementById("doctorSearch");

    if (doctorSearch) {

        doctorSearch.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            const rows = document.querySelectorAll(".doctor-row");

            rows.forEach(function (row) {

                const text = row.innerText.toLowerCase();

                if (text.includes(value)) {

                    row.style.display = "";

                } else {

                    row.style.display = "none";

                }

            });

        });

    }

// =============================
// Live Patient Search
// =============================

const patientSearch = document.getElementById("patientSearch");

if (patientSearch) {

    patientSearch.addEventListener("keyup", function () {

        const value = this.value.toLowerCase();

        const rows = document.querySelectorAll(".patient-row");

        const noPatientRow = document.getElementById("noPatientRow");

        let found = false;

        rows.forEach(function(row){

            const text = row.innerText.toLowerCase();

            if(text.includes(value)){

                row.style.display = "";
                found = true;

            }else{

                row.style.display = "none";

            }

        });

        if(noPatientRow){

            if(found){

                noPatientRow.style.display = "none";

            }else{

                noPatientRow.style.display = "";

            }

        }

    });

}

});
