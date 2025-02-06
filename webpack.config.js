// npm install crypto crypto-browserify node-polyfill-webpack-plugin --legacy-peer-deps
// npm install --save-dev webpack webpack-cli webpack-dev-server html-webpack-plugin clean-webpack-plugin

const NodePolyfillPlugin = require("node-polyfill-webpack-plugin")


const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  entry: './src/main.ts',
  output: {
    path: path.resolve(__dirname, 'wwwebpack'),
    filename: 'bundle.js'
  },
  resolve: {
    extensions: ['.ts', '.js'],
    fallback: {
      "crypto": require.resolve("crypto-browserify")
    }
  },
  target: 'node',
  module: {
    rules: [
      {
        test: /\.ts$/,
        loader: 'ts-loader'
      }
    ]
  },
  plugins: [
    new NodePolyfillPlugin(),
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      template: './www/index.html'
    })
  ],
  devServer: {
    static: path.join(__dirname, 'www'),
    compress: true,
    port: 9000
  }
};

