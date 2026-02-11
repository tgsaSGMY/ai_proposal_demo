# 1. 建置階段
FROM node:20-alpine AS builder

WORKDIR /app

# 複製 package.json 和 lock 檔
COPY package.json package-lock.json ./

# 安裝依賴
RUN npm install

# 複製其餘檔案
COPY . .

# 建置專案 (這會產生 .output 資料夾)
RUN npm run build

# 2. 執行階段
FROM node:20-alpine

WORKDIR /app

# 複製建置好的檔案
COPY --from=builder /app/.output ./.output

EXPOSE 3000

# 設定主機 0.0.0.0 讓外部可訪問，並設定 Port
ENV HOST=0.0.0.0
ENV PORT=3000

# 啟動 Nuxt 伺服器
CMD ["node", ".output/server/index.mjs"]