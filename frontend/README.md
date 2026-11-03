# Frontend — SPA Angular 22

Aplicación de una sola página (SPA) construida con Angular 22, Angular Material
22 y **Signal Forms**. Consume la API de TecnoStock y **no usa SSR** (el build
genera archivos estáticos).

## Requisitos

- Node.js 22+ y npm 10 (`packageManager: npm@10.9.2`).
- Backend en ejecución en `http://localhost:8000` (o ajustar la URL de la API).

## Scripts

```powershell
npm install
npm start                  # servidor de desarrollo en http://localhost:4200
npm run build              # build de producción -> dist/frontend/browser
npm test -- --watch=false  # Vitest + jsdom
```

Para una prueba puntual:

```powershell
npm test -- --watch=false --include src/app/pages/productos/producto-dialog.spec.ts
```

## Configuración

La URL de la API está en `src/environments/environment.ts`:

```ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
};
```

Debe coincidir con `CORS_ORIGINS` del backend. El JWT se guarda en
`sessionStorage` y el `authInterceptor` lo adjunta a cada petición; ante un 401
(excepto en el login) cierra la sesión y redirige a `/login`.

## Estructura

```
src/app/
├── core/          # modelos, AuthService, interceptor, guard, paginador es-PE
├── layout/        # shell con sidenav responsive y barra de usuario
├── pages/
│   ├── login/         # formulario Signal Forms + validaciones
│   ├── dashboard/     # rango de fechas (mes actual por defecto) y KPIs
│   ├── productos/     # filtros con debounce, tabla paginada y diálogo CRUD
│   ├── categorias/    # listado y formulario de alta/edición
│   ├── movimiento/    # entradas y salidas (misma página, según ruta)
│   ├── historial/     # filtros + paginación del servidor
│   └── stock-bajo/    # alertas y enlace directo a reposición
├── services/      # clientes HTTP por recurso
├── shared/        # helpers de formularios y diálogo de confirmación
└── environments/  # URL de la API
```

## Formularios con Signal Forms

Los formularios usan la API experimental estable de Angular 22:

- `form(modeloSignal, schemaFn)` para crear el formulario.
- `[formField]="formulario.campo"` para enlazar `input`, `textarea`, `mat-select`
  y `mat-checkbox` (Material 22 implementa `FORM_FIELD`/`NG_VALUE_ACCESSOR`).
- Validadores `required`, `min`, `minLength`, `maxLength` y `validate` con
  mensajes en español.
- `submit(formulario, { action })` marca los campos como tocados y solo ejecuta
  la acción si el formulario es válido.
- Los mensajes se muestran con `errorDe()` (solo tras tocar el campo).

Signal Forms prohíbe atributos nativos como `min`, `max` o `[disabled]` en nodos
con `[formField]`; por eso las restricciones se declaran en el esquema.

## Reglas de interfaz

- El stock nunca se edita desde el formulario de producto: solo se muestra.
- Al registrar una salida se valida localmente contra el stock actual y el
  backend vuelve a validar dentro de la transacción.
- El dashboard abre con el rango del mes actual y permite cambiarlo.
- `stock-bajo` enlaza a `/entradas?producto=<id>` para reponer directamente.
- Los filtros de productos e historial se aplican con un `effect` y debounce de
  300 ms; el historial pagina en el servidor.

## Pruebas

31 pruebas unitarias con Vitest y jsdom:

- `core/auth.service.spec.ts`: login, almacenamiento en `sessionStorage`, logout,
  rechazo de credenciales y recuperación del usuario.
- `core/auth.guard.spec.ts`: acceso permitido y redirección con `returnUrl`.
- `core/auth.interceptor.spec.ts`: encabezado Bearer, cierre de sesión ante 401
  y excepción del endpoint de login.
- `shared/form-utils.spec.ts`: visibilidad de mensajes según `touched`.
- `pages/productos/producto-dialog.spec.ts`: validaciones, payload (sin stock),
  redondeo de precios y errores de la API.
- `pages/stock-bajo/stock-bajo.spec.ts`: cálculo de faltantes, estado vacío y
  reintento tras error.
- `services/producto.service.spec.ts`: filtros enviados a la API.

## Build

`angular.json` usa `@angular/build:application` con `outputMode: "static"`,
`prerender: false` y `ssr: false`. El resultado en `dist/frontend/browser` puede
publicarse en cualquier servidor estático; las rutas internas deben redirigir a
`index.html` (fallback de SPA).

## Limitaciones conocidas

- El proyecto no incluye pruebas end-to-end con navegador; la integración se
  verificó con pruebas de API reales y pruebas unitarias de componentes.
- La aplicación asume que la API está disponible; no hay modo offline.
