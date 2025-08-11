// Este arquivo pode ser usado para funções JavaScript adicionais
// Atualmente a maior parte do JavaScript está nos templates

// Função para formatar a data
function formatarData(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 2) {
        value = value.substring(0, 2) + '/' + value.substring(2);
    }
    if (value.length > 5) {
        value = value.substring(0, 5) + '/' + value.substring(5, 9);
    }
    input.value = value;
}

// Adiciona máscara de data aos campos de data
document.addEventListener('DOMContentLoaded', function() {
    const dataInputs = document.querySelectorAll('input[type="text"][placeholder="DD/MM/AAAA"]');
    dataInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatarData(this);
        });
    });
});