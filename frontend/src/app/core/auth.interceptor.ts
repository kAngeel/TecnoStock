import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { AuthService } from './auth.service';

/** Agrega el token JWT y cierra la sesión si el servidor responde 401. */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const token = auth.token();

  const peticion = token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(peticion).pipe(
    catchError((error: unknown) => {
      const esLogin = request.url.includes('/auth/login');
      if (error instanceof HttpErrorResponse && error.status === 401 && !esLogin) {
        auth.cerrarSesion();
      }
      return throwError(() => error);
    }),
  );
};
