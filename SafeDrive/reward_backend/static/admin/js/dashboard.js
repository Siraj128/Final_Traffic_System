// Dashboard Logic

const API_BASE = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", async () => {
    await fetchDashboardStats();
    await fetchRedemptions();
});

async function fetchDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/dashboard`);
        const data = await response.json();

        // Update KPIs
        document.getElementById("total-drivers").innerText = data.stats.total_drivers;
        document.getElementById("total-rewards").innerText = data.stats.total_rewards_issued;
        document.getElementById("total-violations").innerText = data.stats.total_violations;
        document.getElementById("pending-redemptions").innerText = data.stats.pending_redemptions;

        // Render Charts
        renderTierChart(data.tiers);
        renderRiskChart(data.risks);

    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

async function fetchRedemptions() {
    try {
        const response = await fetch(`${API_BASE}/admin/redemptions`);
        const data = await response.json();
        const tableBody = document.getElementById("redemption-table-body");
        tableBody.innerHTML = "";

        // Show last 5
        data.slice(0, 5).forEach(txn => {
            const row = `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4">#${txn.transaction_id}</td>
                    <td class="px-6 py-4 font-semibold text-gray-800">${txn.plate_number}</td>
                    <td class="px-6 py-4">${txn.reward ? txn.reward.title : 'Unknown Reward'}</td>
                    <td class="px-6 py-4">${txn.points_spent}</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 rounded text-xs font-semibold ${getStatusColor(txn.status)}">
                            ${txn.status}
                        </span>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } catch (e) {
        console.error("Error fetching redemptions:", e);
    }
}

function getStatusColor(status) {
    if (status === "SUCCESS" || status === "APPROVED") return "bg-green-100 text-green-700";
    if (status === "PENDING") return "bg-orange-100 text-orange-700";
    if (status === "REJECTED") return "bg-red-100 text-red-700";
    return "bg-gray-100 text-gray-700";
}

function renderTierChart(tiers) {
    const ctx = document.getElementById('tierChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Bronze', 'Silver', 'Gold', 'Platinum'],
            datasets: [{
                data: [tiers.bronze, tiers.silver, tiers.gold, tiers.platinum],
                backgroundColor: [
                    '#CD7F32', // Bronze
                    '#C0C0C0', // Silver
                    '#FFD700', // Gold
                    '#E5E4E2'  // Platinum
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

function renderRiskChart(risks) {
    const ctx = document.getElementById('riskChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Safe', 'Moderate', 'High Risk'],
            datasets: [{
                label: 'Drivers',
                data: [risks.safe, risks.moderate, risks.high_risk],
                backgroundColor: [
                    '#10B981', // Green
                    '#F59E0B', // Orange
                    '#EF4444'  // Red
                ],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
