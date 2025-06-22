document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatHistory = document.getElementById('chatHistory');
    const infoTitle = document.getElementById('infoTitle');
    const metricContainer = document.getElementById('metricContainer');
    const stockInfo = document.getElementById('stock-info');
    const stockDetails = document.getElementById('stockDetails');

    function interpret(metric, value) {
        let val = parseFloat(String(value).replace(/[^0-9.-]/g, ''));
        let comment = '-';
        let status = 'neutral';
        switch (metric) {
            case 'per':
                if (val <= 15) { status = 'good'; comment = '저평가'; }
                else if (val <= 25) { status = 'neutral'; comment = '보통'; }
                else { status = 'bad'; comment = '고평가'; }
                break;
            case 'roe':
                if (val >= 15) { status = 'good'; comment = '우수'; }
                else if (val >= 10) { status = 'neutral'; comment = '양호'; }
                else { status = 'bad'; comment = '낮음'; }
                break;
            case 'debt_ratio':
                if (val < 50) { status = 'good'; comment = '건전'; }
                else if (val < 100) { status = 'neutral'; comment = '주의'; }
                else { status = 'bad'; comment = '위험'; }
                break;
            case 'sales':
            case 'market_cap':
                if (!isNaN(val) && val >= 100) { status = 'good'; comment = '대형'; }
                else if (!isNaN(val) && val >= 50) { status = 'neutral'; comment = '중간'; }
                else { status = 'bad'; comment = '소형'; }
                break;
        }
        return { comment, status };
    }

    function updateMetrics(info) {
        metricContainer.innerHTML = '';
        if (!info || !info.name) {
            infoTitle.textContent = '종목을 선택하면 지표가 표시됩니다.';
            return;
        }
        infoTitle.textContent = `${info.name}`;
        const metrics = [
            { key: 'per', label: 'PER', icon: '📈' },
            { key: 'roe', label: 'ROE', icon: '💸' },
            { key: 'debt_ratio', label: '부채비율', icon: '🏦' },
            { key: 'sales', label: '매출액', icon: '💰' },
            { key: 'market_cap', label: '시가총액', icon: '🏢' },
            { key: 'main_products', label: '주요 제품', icon: '📦' },
            { key: 'return_1y', label: '1년 수익률', icon: '📈' },
            { key: 'return_3y', label: '3년 수익률', icon: '📈' },
        ];
        metrics.forEach(m => {
            const value = info[m.key];
            if (value == null) return;
            let displayValue = value;
            if (['return_1y','return_3y'].includes(m.key)) {
                displayValue = value + '%';
            }
            const { comment, status } = interpret(m.key, value);
            const card = document.createElement('div');
            card.className = `metric-card ${status}`;
            card.innerHTML = `<div class="metric-title">${m.icon} ${m.label}</div>` +
                             `<div class="metric-value">${displayValue}</div>` +
                             `<div class="metric-comment">${comment}</div>`;
            metricContainer.appendChild(card);
        });
    }

    function updateRightPanel(info) {
        stockDetails.innerHTML = '';
        if (!info) {
            stockDetails.textContent = '종목 정보를 찾을 수 없습니다.';
            return;
        }
        let html = '';
        if (info.name) {
            html += `<h2>${info.name}</h2>`;
        }
        if (info.summary) {
            html += `<span class="stock-summary">${info.summary}</span>`;
        }
        if (info.description) {
            html += `<p>${info.description}</p>`;
        }
        if (info.products && info.products.length) {
            html += '<ul>' + info.products.map(p => `<li>${p}</li>`).join('') + '</ul>';
        }
        stockDetails.innerHTML = html;
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = 'message ' + sender;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showLoading() {
        const div = document.createElement('div');
        div.className = 'message bot loading';
        div.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return div;
    }

    function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';
        const loader = showLoading();

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            loader.remove();
            addMessage(data.reply, 'bot');
            if (data.main_products) {
                addMessage(`주요 제품: ${data.main_products}`, 'bot');
            }
            updateMetrics(data);
            updateRightPanel(data.stock_info || null);
        })
        .catch(() => {
            loader.remove();
            addMessage('오류가 발생했습니다.', 'bot');
        });
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
});
