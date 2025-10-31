const socket = io();

const cpuCtx = document.getElementById("cpuChart").getContext("2d");
const memCtx = document.getElementById("memChart").getContext("2d");

let cpuChart = new Chart(cpuCtx, {
  type: "bar",
  data: { labels: [], datasets: [{ label: "CPU Usage (cores)", data: [] }] },
});

let memChart = new Chart(memCtx, {
  type: "bar",
  data: { labels: [], datasets: [{ label: "Memory Usage (MB)", data: [] }] },
});

socket.on("metrics_update", (data) => {
  console.log("Received metrics:", data);

  // Update table
  const tbody = document.querySelector("#vmTable tbody");
  tbody.innerHTML = "";
  data.forEach((vm) => {
    const row = `<tr>
      <td>${vm.name}</td>
      <td>${vm.namespace}</td>
      <td>${vm.cpu.toFixed(3)}</td>
      <td>${(vm.memory / (1024*1024)).toFixed(1)}</td>
    </tr>`;
    tbody.innerHTML += row;
  });

  // Update charts
  cpuChart.data.labels = data.map((vm) => vm.name);
  cpuChart.data.datasets[0].data = data.map((vm) => vm.cpu);
  cpuChart.update();

  memChart.data.labels = data.map((vm) => vm.name);
  memChart.data.datasets[0].data = data.map((vm) => vm.memory / (1024 * 1024));
  memChart.update();
});
