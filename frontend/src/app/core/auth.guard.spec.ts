import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { authGuard } from './auth.guard';

@Component({ template: '' })
class PantallaVacia {}

describe('authGuard', () => {
  let router: Router;

  beforeEach(() => {
    sessionStorage.clear();

    TestBed.configureTestingModule({
      providers: [provideRouter([{ path: 'login', component: PantallaVacia }])],
    });

    router = TestBed.inject(Router);
  });

  afterEach(() => sessionStorage.clear());

  function ejecutar(url: string) {
    return TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
    );
  }

  it('permite el acceso cuando existe un token', () => {
    sessionStorage.setItem('tecnostock.token', 'cabecera.cuerpo.firma');

    expect(ejecutar('/dashboard')).toBe(true);
  });

  it('redirige al login y conserva la URL solicitada sin token', () => {
    const resultado = ejecutar('/productos');

    expect(resultado instanceof UrlTree).toBe(true);
    const url = router.serializeUrl(resultado as UrlTree);
    expect(url).toContain('/login');
    expect(url).toContain('returnUrl=%2Fproductos');
  });
});
