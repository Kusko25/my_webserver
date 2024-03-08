const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');


module.exports = {
  resolve: {
    modules: [path.resolve(__dirname), 'node_modules'],
  },
  plugins: [
    new MiniCssExtractPlugin(options = { filename: 'css/webpack/[name]-index-bundle.css' }),
  ],
  entry: {
    main: './src/js/main.js'
  },
  output: {
    filename: 'js/webpack/[name]-index-bundle.js',  // output bundle file name
    path: path.resolve(__dirname, './../static'),  // path to our Django static directory
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        options: { presets: ["@babel/preset-env", "@babel/preset-react"] }
      },
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader'
        ]
      },
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          'sass-loader'
        ]
      },
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/webpack/[name].[ext]'
        }
      }
    ]
  }
};

