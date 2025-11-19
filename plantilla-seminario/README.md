# Plantilla del Proyecto del Seminario

| Código | Nombre | Correo |
|:---|:---|:---|
| 542378923 | Daniel Camilo Rosero Pantoja | daniel.rosero.4511@miremington.edu.co |


---

## Objetivos del Seminario

* Diseñar microservicios independientes que se comunican entre sí.
* Implementar API RESTful con FastAPI.
* Utilizar diferentes tipos de bases de datos para cada microservicio.
* Implementar un front-end básico para hacer uso de los microservicios.
* Contenerizar aplicaciones con Docker.
* Orquestar la infraestructura con Docker Compose.


### Ejecutar el Proyecto

Una vez que tengas tus servicios configurados, puedes levantar todo el stack con un solo comando:

```bash
docker-compose up --build
```

Esto construirá las imágenes y ejecutará todos los contenedores. Podrás acceder al frontend en `http://localhost:5000` y al API Gateway en `http://localhost:8000/docs`.
