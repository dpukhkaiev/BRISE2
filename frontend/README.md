# Frontend – Vue 3 + TypeScript (FSD)

This project is a frontend application built with Vue 3, TypeScript, and Vite.  
The architecture follows the Feature-Sliced Design (FSD) methodology to ensure a scalable and maintainable codebase.

## Technologies
- Vue 3
- TypeScript
- Vite

## Architecture
The project is structured according to the Feature-Sliced Design (FSD) approach, separating the code into distinct layers:

- **app** – application setup and global configuration  
- **pages** – application views  
- **widgets** – larger UI blocks  
- **features** – business features  
- **entities** – domain models and business logic  
- **shared** – reusable components and utilities  

## Goal
The goal is to improve scalability, maintainability, and separation of concerns within the frontend application. Additionally, the chosen architecture aims to slow down software aging by promoting a clean, modular, and easily extensible codebase.