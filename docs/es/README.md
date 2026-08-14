# NetBox Force — Guía (español)

[← Todos los idiomas](../README.md) · [README del proyecto](../../README.md) · [Historial de cambios](../../CHANGELOG.md)

---

## 1. Qué hace el plugin

NetBox registra *qué* ha cambiado. NetBox Force decide *si el cambio está
permitido siquiera*, y puede exigir un motivo antes de dejarlo pasar.

Se sitúa entre cada operación de guardado o borrado y la base de datos. Antes de
escribir un cambio puede comprobar:

- que se ha indicado un comentario de registro y que es suficientemente largo
- que el comentario no consiste únicamente en palabras vacías
- que el comentario menciona un número de ticket
- que el cambio ocurre dentro de una ventana de tiempo aprobada
- que los valores de los campos siguen un patrón de nombres
- que los campos obligatorios están realmente rellenados

Se acompaña de dos módulos más:

- **Gestión de parches** — estado de parcheo, sistema operativo, responsables e
  historial de actualizaciones por máquina virtual o servidor físico,
  opcionalmente alimentado desde CheckMK.
- **Graylog** — envía eventos de auditoría hacia fuera y trae información de
  registro junto al objeto al que pertenece.

Todo es opcional. Tras la instalación solo está activa la comprobación de
presencia del comentario, con un mínimo de dos caracteres. El resto se activa
desde la interfaz web.

---

## 2. Requisitos

| Componente | Versión | Notas |
|---|---|---|
| NetBox | 4.0.0 o posterior | |
| Python | 3.10 o posterior | |
| PostgreSQL | — | Lo requiere el propio NetBox |
| `cryptography` | cualquiera | Viene con NetBox. Sin él, el secreto de CheckMK y el token de Graylog se guardan sin cifrar, y el plugin lo indica en la página de ajustes |
| `requests` | cualquiera | Viene con NetBox. Necesario para CheckMK y Graylog |
| Proceso RQ | — | Solo para el sondeo programado de CheckMK y Graylog. Sin él ambos siguen funcionando bajo demanda, y la página lo indica |

---

## 3. Instalación

### 3.1 Instalar el paquete

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Registrar el plugin

En `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Ejecutar las migraciones

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Reiniciar NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <contenedor> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <contenedor> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <contenedor>
```

En la imagen de LinuxServer.io **no** use scripts `custom-cont-init.d` para la
instalación. Se ejecutan *después* de los scripts de inicio de NetBox, lo que
puede provocar fallos en las migraciones. Los Docker Mods se ejecutan antes.

Una instalación hecha dentro del sistema de archivos del contenedor no sobrevive a
una actualización de imagen. Añada el plugin al mecanismo persistente de
instalación de plugins de la imagen, o desaparecerá tras el siguiente pull.

---

## 4. Actualización

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` hace falta porque pip guarda en caché por
número de versión y de otro modo omitiría reconstruir la misma versión.

**Compruebe antes de reiniciar.** Este paso importa el plugin sin tocar el proceso
en ejecución. Si informa de un error, no reinicie: el NetBox en marcha sigue
teniendo el código anterior en memoria y continúa funcionando:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Después:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Volver atrás

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Normalmente no hace falta revertir las migraciones. Las columnas adicionales no
molestan al código antiguo: sencillamente no las conoce. Aun así, haga una copia
de la base de datos antes de actualizar.

---

## 5. Archivo de configuración

`PLUGINS_CONFIG` fija **solo los valores iniciales**. Tras el primer arranque cada
ajuste se gestiona en la interfaz web y se guarda en la base de datos.

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
        'checkmk_secret': '',
    },
}
```

| Ajuste | Valor por defecto | Significado |
|---|---|---|
| `min_length` | `2` | Caracteres mínimos en un comentario de registro |
| `exempt_users` | ver arriba | Usuarios exentos de toda comprobación, sin distinguir mayúsculas |
| `enforce_on_create` | `False` | Exigir comentario también al crear objetos |
| `enforce_on_delete` | `True` | Exigir comentario también al borrar objetos |
| `extra_exempt_models` | `[]` | Más modelos exentos, formato `app.model` |
| `checkmk_secret` | `''` | Opcional. Mantiene el secreto de CheckMK completamente fuera de la base de datos; entonces tiene prioridad sobre el campo de la interfaz |

---

## 6. Las páginas

Los superusuarios encuentran **NetBox Force** en la barra lateral. Todas las
páginas están restringidas a superusuarios salvo que se indique lo contrario.

| Página | Propósito |
|---|---|
| **Ajustes** | Todas las reglas de aplicación, exenciones, módulos, webhook, CheckMK |
| **Reglas de validación** | Patrones de nombres y campos obligatorios, por modelo y campo |
| **Políticas por modelo** | Excepciones a los ajustes globales, por modelo |
| **Infracciones** | Registro filtrable de cada cambio bloqueado, exportable a CSV |
| **Graylog** | Envío y lectura, véanse las secciones 7 y 8 |
| **Panel** | Estadísticas: qué funciones están activas, cambios bloqueados, usuarios más frecuentes, tendencia de 30 días |
| **Plantillas de importación** | Plantillas CSV descargables para la importación masiva de NetBox. Visibles para todos los usuarios autenticados cuando está activado |
| **Guía** | Página de texto libre para sus propios usuarios. Visible para todos los usuarios autenticados cuando está activada |
| **Gestión de parches** | Véase la sección 9 |

Dos ajustes merecen mención aparte:

- **Interruptor global** — suspende todas las comprobaciones, por ejemplo durante
  una ventana de mantenimiento.
- **Modo de prueba (dry-run)** — registra las infracciones sin bloquear nada. Es
  la forma correcta de introducir una regla nueva: se ve qué *se habría*
  bloqueado antes de detener a nadie de verdad.

---

## 7. Graylog — envío

Envía eventos de auditoría de NetBox a Graylog mediante GELF.

### Para qué

Tres cosas no se registran en ningún otro sitio de NetBox:

- **Inicios de sesión fallidos.** NetBox no los guarda en absoluto.
- **IP de origen y agente de usuario** de un cambio. El registro de cambios de
  NetBox no lleva ninguno de los dos.
- **Cambios en los propios ajustes del plugin.** No están cubiertos por el
  registro de cambios de NetBox, así que desactivar la aplicación de reglas no
  dejaba antes ningún rastro.

### Configuración

En la página **Graylog**, mitad superior: host, puerto, transporte. Después
*Enviar evento de prueba*.

Empiece con **UDP**. Si no llega nada, cambie a **TCP**: por diseño, UDP no puede
informar de un fallo y TCP sí. Eso distingue «puerto equivocado» de «mensaje
descartado».

| Transporte | Confirma la entrega | Cifrado |
|---|---|---|
| UDP | no | no |
| TCP | sí | no |
| TCP + TLS | sí | sí |
| HTTP | sí | no |
| HTTPS | sí | sí |

UDP es correcto dentro de una red local e incorrecto a través de internet.

### Qué se envía

Una fila por tipo de evento, cada una con casilla y nivel de gravedad syslog:
objeto creado, modificado, eliminado; inicio de sesión; cierre de sesión; inicio
de sesión fallido; cambio bloqueado; ajustes del plugin modificados.

### Volumen

Una petición que modifique más objetos que el umbral configurado se comunica como
**un único evento resumen**. Importar 500 dispositivos es una operación: 500
líneas casi idénticas la hacen más difícil de ver, no más fácil.

Resumir en lugar de limitar el ritmo es una decisión deliberada. Una cola que se
vacía más despacio de lo que se llena descarta los eventos *más nuevos*, que es
justo la mitad equivocada.

### Nombres de campo

Todos los eventos llevan los mismos campos, para que las búsquedas sigan siendo
sencillas:

```
_app          netbox_force
_category     object_change | auth | violation | settings
_event        object_created, login_failed, …
_username
_client_ip
_user_agent
_object_type  dcim.device
_object_id
_object_name
_action       create | update | delete
_changed_fields
_request_id
_netbox_url
_outside_business_hours
```

`_request_id` agrupa todo lo que ha cambiado una petición. Cuarenta dispositivos
editados a la vez son una operación, no cuarenta enigmas.

### Tres cosas que conviene saber

- **Una caída de Graylog no puede ralentizar ni hacer fallar un guardado en
  NetBox.** Los eventos van a una cola acotada que vacía un hilo en segundo plano.
  Cuando la cola se llena, los eventos nuevos se descartan y se cuentan, y el
  contador se muestra en la página.
- **El texto del mensaje siempre está en inglés**, sea cual sea el idioma de la
  interfaz. Las consultas de alerta de Graylog se basan en ese texto; traducirlo
  rompería en silencio todas las alertas en cuanto alguien cambiara el idioma.
- **La IP del cliente se lee de `X-Forwarded-For`** cuando está presente. Esa
  cabecera la envía el cliente y puede falsificarse si NetBox es accesible sin un
  proxy inverso delante.

---

## 8. Graylog — lectura

Trae información de Graylog a NetBox para poder juzgar un host sin abrir una
segunda pestaña.

### Configuración

Mitad inferior de la página **Graylog**: dirección web y token de API, después
*Probar conexión*. El resultado indica la versión de Graylog, la forma de API de
búsqueda detectada, los orígenes más ruidosos y los streams disponibles. *Sondear
ahora* ejecuta un sondeo inmediato.

**Emita el token para un usuario de Graylog con rol de solo lectura.** Eso, y no
el código de este plugin, es lo que garantiza que Graylog no pueda alterarse desde
NetBox.

### Qué significa aquí «solo lectura», con precisión

Cada llamada obtiene datos o pide a Graylog que ejecute una búsqueda. El endpoint
de búsqueda antiguo es un `GET` simple. La API de búsqueda Views más reciente no:
requiere un `POST` para registrar una búsqueda y otro para ejecutarla. Eso crea un
objeto de búsqueda efímero dentro de Graylog y devuelve resultados; no modifica
datos almacenados. Si en su entorno solo se acepta `GET`, fije la forma de
búsqueda a `legacy` en los ajustes.

### Emparejar orígenes con objetos de NetBox

Exacto, en este orden, gana la primera coincidencia:

| | Regla |
|---|---|
| 1 | **Asignación manual** — una vez puesta, siempre prevalece |
| 2 | **Dirección IP** — el origen contra todas las IP del objeto |
| 3 | **Nombre de host**, sin distinguir mayúsculas |
| 4 | **Nombre de host tras quitar un sufijo de dominio configurado** |

Todo lo demás queda sin asignar y se lista como tal.

**No hay emparejamiento aproximado, deliberadamente.** `srv-web-01` y `srv-web-02`
se diferencian en un carácter, así que cualquier medida de similitud los llama
coincidencia del 96 % siendo dos máquinas distintas. En un esquema de nombres
numerado — es decir, en cualquier NetBox que merezca el nombre — el candidato más
parecido es sistemáticamente el equivocado. Los registros acabarían archivados
bajo el servidor vecino y nadie se daría cuenta. La similitud solo sirve para
**ordenar** las sugerencias junto a un origen sin asignar; nunca asigna nada.

Si delante de Graylog hay un relé syslog central, todos los mensajes llevan la
dirección del relé y la regla 2 no acierta nada útil. Entonces el campo de origen
debe llevar el nombre de host, para lo cual están las reglas 3 y 4.

### Las páginas

- **Orígenes** — todo lo que Graylog informa, con contadores, filtrable por
  asignados, sin asignar, silenciosos, nunca vistos e ignorados.
- **Silenciosos** — asignados en NetBox pero sin enviar nada. Muertos, mal
  configurados o un resto. Ninguno de los dos sistemas lo detecta por sí solo.
- **Nunca vistos en Graylog** — la otra mitad de la comprobación cruzada.
- **Clúster** — nodos con semáforo verde/amarillo/rojo, salud del indexador,
  retraso del diario, cada nodo enlazado a su máquina virtual en NetBox.
- **En el objeto** — los dispositivos y máquinas virtuales con un origen asignado
  reciben un panel de Graylog con contadores, mensajes recientes bajo demanda y un
  enlace a Graylog.

### Carga y seguridad

- Un sondeo es **una única consulta agrupada para todos los hosts**, no una
  consulta por dispositivo. Una sede con 800 dispositivos cuesta tres peticiones.
- El panel del clúster y la lista de mensajes se cargan **después** de renderizar
  la página. Un Graylog lento o caído produce un panel vacío, nunca una página de
  NetBox colgada.
- El emparejamiento vive en la tabla propia del plugin. **Graylog nunca escribe en
  un objeto central de NetBox**: quitar el plugin elimina el emparejamiento y deja
  NetBox intacto.
- El endpoint de mensajes solo responde para un origen asignado a un objeto que
  quien llama tiene permiso de ver.

---

## 9. Gestión de parches y CheckMK

Lleva el estado de parcheo, el sistema operativo, los responsables y el historial
de actualizaciones por máquina virtual o servidor físico.

- **Estado** verde / amarillo / rojo, mantenido a mano o leído de CheckMK.
- **Umbral de retraso** — las entradas sin parchear en N días se marcan como
  atrasadas.
- **Escalado** — una entrada que lleva N días en *amarillo* pasa sola a *rojo*.
- **Contactos** — administrador y responsable del proceso a partir de los objetos
  de contacto de NetBox.
- **Historial de actualizaciones** — una entrada por pasada de parcheo, con número
  de ticket y nota.
- **El acceso** se concede por nombre de grupo de NetBox en los ajustes del
  plugin, no mediante permisos de Django.

### CheckMK

La integración es un **pull**: NetBox lee de CheckMK. No se escribe nada en
CheckMK, así que basta un usuario de automatización de solo lectura.

Se configura en la página de ajustes: URL del sitio, usuario de automatización,
secreto, filtro de servicios e intervalo de sincronización. El secreto se guarda
cifrado y no se vuelve a mostrar.

Una sincronización detenida es el fallo que más duele, porque la página sigue
mostrando un estado de parcheo que dejó de ser cierto en silencio. Por eso el
panel dice sin rodeos cuándo la última sincronización correcta es más antigua que
el doble del intervalo configurado.

---

## 10. Resolución de problemas

**El plugin no aparece en la barra lateral.**
¿Está `PLUGINS` en `configuration.py`? ¿Se han ejecutado las migraciones? ¿Se ha
reiniciado NetBox? Las etiquetas de la barra lateral solo se actualizan al
reiniciar; las pestañas dentro del plugin, de inmediato.

**Los cambios no se bloquean.**
Compruebe, en este orden: el interruptor global, el modo de prueba, si su usuario
está en los usuarios o grupos exentos, y si una política por modelo desactiva la
aplicación para ese modelo.

**Una página informa de una columna que falta.**
Las migraciones no se han ejecutado, o solo en parte.
`python manage.py migrate netbox_force`.

**«No hay ningún proceso en segundo plano».**
`netbox-rq` no está en marcha. La sincronización de CheckMK y el sondeo de Graylog
solo se ejecutan al pulsar el botón.

**No llega nada a Graylog.**
Cambie el transporte de UDP a TCP. UDP no puede informar de un fallo; TCP sí, y su
mensaje de error dice si el puerto es incorrecto o si el mensaje fue rechazado.

**El panel de Graylog en un dispositivo queda vacío.**
El dispositivo no tiene origen asignado. Abra *Orígenes → Sin asignar* y asígnelo,
o añada su sufijo de dominio en los ajustes para que el FQDN pueda acortarse.

**Tras cambiar `SECRET_KEY`, el secreto de CheckMK o el token de Graylog dejan de funcionar.**
Ambos están cifrados con una clave derivada de `SECRET_KEY`. Hay que volver a
introducirlos.

---

## 11. Cambiar el idioma

El idioma es un ajuste **por instalación**, no por usuario. Se cambia en la página
de ajustes.

Las pestañas y páginas dentro del plugin cambian de inmediato. Las etiquetas de la
barra lateral se construyen una sola vez al arrancar y solo cambian tras reiniciar
NetBox.

Los mensajes que se muestran a los usuarios al bloquear siguen este ajuste. Los
mensajes de error de la API y los enviados a Graylog permanecen en inglés; véase
la nota en el [índice de documentación](../README.md).

---

## 12. Licencia

AGPL-3.0. Véase [LICENSE](../../LICENSE).
