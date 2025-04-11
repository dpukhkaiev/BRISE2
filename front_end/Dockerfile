# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM brisedev/front-end-prod:latest as build-stage
COPY ./ /app/
ARG configuration=production
RUN npm run build -- --output-path=./dist/out --configuration $configuration

Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1.19.3
COPY --from=build-stage /app/dist/out/ /usr/share/nginx/html
Copy the default nginx.conf provided by tiangolo/node-frontend
COPY --from=build-stage /nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
