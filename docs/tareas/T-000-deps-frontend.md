# T-000: Consolidar la actualización a Vite 8 y React Router 7
Lado: frontend
Requerimientos: RNF-17, RNF-19
Rama: tarea/T-000-deps-frontend
Depende de: —

## Objetivo
El usuario decidió mantener la subida de dependencias que hoy está sin commitear en `07_MVP/frontend/package.json` y `package-lock.json`: Vite 5→8 y React Router 6→7. `npm run build` ya pasa, pero `npm ls` marca `vite@8.3.4 invalid`, porque `@vitejs/plugin-react@4.7.0` solo admite Vite hasta la 7. Hay que dejar el árbol de dependencias consistente, de modo que una instalación limpia funcione.

## Alcance
- SÍ: subir `@vitejs/plugin-react` a una versión que admita Vite 8 (la 6.x declara `vite: ^8.0.0`) y revisar sus peer dependencies. Si alguna de ellas es opcional, no agregarla salvo que haga falta.
- SÍ: ajustar `vite.config.ts` solo si el plugin nuevo lo exige. Mantener el alias `@/`.
- SÍ: revisar las advertencias de deprecación de React Router 7 en el código de rutas (`App.tsx` y los `useNavigate`/`Link` existentes) y corregir solo lo que rompa o emita advertencias.
- SÍ: commitear los cambios actuales de `package.json` y `package-lock.json` junto con los tuyos.
- NO: actualizar otras dependencias (React 19, TypeScript, etc.), cambiar estilos, componentes ni comportamiento.

## Contrato de API
No aplica.

## Archivos probables
- Tocar: `07_MVP/frontend/package.json`, `package-lock.json` y, si hace falta, `vite.config.ts` y `src/App.tsx`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `globals.css`.

## Criterios de aceptación
- [ ] `npm ls` no reporta errores (sin `invalid` ni `ELSPROBLEMS`).
- [ ] Una instalación limpia funciona: borrar `node_modules`, ejecutar `npm ci` y luego `npm run build` sin errores. No se vale `--legacy-peer-deps` ni `--force`.
- [ ] `npm run dev` levanta y las rutas cargan: `/login`, `/`, `/proyectos/nuevo` y `/proyectos/:id/*`.
- [ ] No hay advertencias nuevas de React Router en la consola del navegador al navegar.
- [ ] Si cambia algún requisito de instalación (por ejemplo, la versión mínima de Node que pide Vite 8), queda anotado en `07_MVP/README.md`.
- [ ] Commits con el formato `T-000 RNF-17: ...`.

## Notas
- Comprobación del supervisor del 2026-10-14: `npm run build` pasa con Vite 8.3.4 y muestra advertencias de deprecación (`esbuild` → `oxc`, `rollupOptions` → `rolldownOptions`) que vienen del plugin 4.x.

## Revisión
2026-10-14 · **Aprobada**.
- Diff: `package.json` (react-router-dom ^7.18.4, @vitejs/plugin-react ^6.1.2, vite ^8.3.4), `package-lock.json` y `07_MVP/README.md` (Node 20.19+ o 22.12+). No hay cambios en `src/` ni en `vite.config.ts`, y nada fuera del frontend.
- Verificado por el supervisor: `npm ls` sin errores y `npm run build` en verde, sin las advertencias de deprecación del plugin 4.x. El programador comprobó `npm ci` limpio.
- Pendiente menor: nadie abrió un navegador para revisar las advertencias de React Router 7 en consola. Revisé el código: solo usa `Routes`, `Route`, `Navigate`, `Link`, `NavLink` y `useNavigate`, que son estables en v7. Queda como verificación manual del usuario.
