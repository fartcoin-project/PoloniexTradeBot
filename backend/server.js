require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const ccxt = require('ccxt');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

let tradebot = null;

// Initialize Poloniex API with user keys
const initPoloniex = (apiKey= SECRET_API_KEY, secretKey= SECRET_API_SECRET) => {
    return new ccxt.poloniex({
        apiKey: apiKey,
        secret: secretKey,
        options: { createMarketBuyOrderRequiresPrice: false },
    });
};

// Fetch available trading pairs
app.get('/api/trading-pairs', async (req, res) => {
    try {
        const exchange = new ccxt.poloniex();
        const markets = await exchange.loadMarkets();
        res.json(Object.keys(markets));
    } catch (error) {
        res.status(500).json({ error: 'Error fetching trading pairs' });
    }
});

// Start TradeBot
app.post('/api/start', (req, res) => {
    const { apiKey= SECRET_API_KEY, secretKey= SECRET_API_SECRET, budget, excludeList } = req.body;

    try {
        tradebot = initPoloniex(apiKey, secretKey);
        res.json({ message: 'TradeBot started successfully', budget, excludeList });
    } catch (error) {
        res.status(500).json({ error: 'Error starting TradeBot' });
    }
});

// Stop TradeBot
app.post('/api/stop', (req, res) => {
    tradebot = null;
    res.json({ message: 'TradeBot stopped' });
});

// Fetch open orders
app.get('/api/orders', async (req, res) => {
    if (!tradebot) {
        return res.status(400).json({ error: 'TradeBot not started' });
    }

    try {
        const orders = await tradebot.fetchOpenOrders();
        res.json(orders);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching orders' });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
