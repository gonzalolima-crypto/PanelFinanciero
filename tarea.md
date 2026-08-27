ago 27, 2026

## **Reunión del 27 ago 2026 a las 14:29 GMT-03:00**

Registros de la reunión [Transcripción](https://docs.google.com/document/d/1EjQJOMvbZDSP2GMfonGrEROlLZ7kOvKT5gzPscbPCfY/edit?usp=drive_web&tab=t.x0kwtoxcmpj6) 

### **Resumen**

La sesión revisó la arquitectura de software, las restricciones de interfaces y estrategias para el futuro despliegue web.

**Limitaciones técnicas y arquitectura**  
Las llaves de interfaz de programación de aplicaciones gratuitas presentan restricciones de tiempo. El sistema utilizará Flask y base de datos SQLite 3 para soportar archivos.

**Proceso de desarrollo local**  
El desarrollo guiado por especificaciones permite evaluar la estabilidad del sistema. La validación local facilita identificar errores críticos antes de la migración.

**Despliegue en servidores web**  
Se decidió utilizar repositorios de GitHub o GitLab para publicar la aplicación en servidores gratuitos tras completar las pruebas locales.

### **Decisiones**

## Acordada

* **Arquitectura técnica definida** La arquitectura de la aplicación utilizará un backend en Flask con Python y una base de datos SQLite 3 para gestionar la información.

* **Estrategia de alojamiento definida** La aplicación se publicará en un servicio de alojamiento gratuito mediante un repositorio de código como GitHub o GitLab tras finalizar las pruebas locales.

**Actualizamos la sección Decisiones** con tus comentarios.

Danos tu opinión: [Útil](https://google.qualtrics.com/jfe/form/SV_5bXzKQfylMIhSXc?isHelpful=True&entryPoint=decisions&confid=53XtE_eQmMiSXnB6JkfcDxIQOBEBMgUIigIgABgFCA&isGoogler=False) o [Poco útil](https://google.qualtrics.com/jfe/form/SV_5bXzKQfylMIhSXc?isHelpful=False&entryPoint=decisions&confid=53XtE_eQmMiSXnB6JkfcDxIQOBEBMgUIigIgABgFCA&isGoogler=False)

### **Próximos pasos**

- [ ] \[Gonzalo D'Oliveira Lima\] Solicitar API Key: Solicitar una API Key de un LLM para utilizar en la demostración del agente.

- [ ] \[Gonzalo D'Oliveira Lima\] Desarrollar Aplicativo: Desarrollar el backend en Python con Flask y SQLite e implementar funciones de carga de archivos y transcripción de voz.

- [ ] \[Gonzalo D'Oliveira Lima\] Publicar Repositorio: Subir el código finalizado a un repositorio de GitHub o GitLab para su posterior despliegue en un servicio de hosting.

### **Detalles**

* **Concepto y limitaciones de las llaves API**: El problema principal radica en comprender el funcionamiento de las llaves API para conectar con modelos de lenguaje y las restricciones operativas de las versiones gratuitas. Gabriel Angel de Jesus Rumani compara la llave API ("API Key") con una línea telefónica o una llave que abre el acceso hacia una inteligencia artificial. Gonzalo D'Oliveira Lima consulta sobre la ruta de conexión de ida y vuelta ([00:23:20](?tab=t.x0kwtoxcmpj6#heading=h.883ul0ny6wqc)). Gabriel Angel de Jesus Rumani advierte que las llaves API gratuitas otorgan un tiempo de uso muy limitado, lo que puede provocar un error de tiempo de espera agotado ("time out") al ejecutar tareas complejas como iteraciones de carpetas o reglas automáticas, haciendo necesario contar con un recurso adecuado para pruebas.

* **Arquitectura y funcionalidades de la aplicación**: Se aborda la evolución del proyecto desde un prototipo en maqueta HTML hacia un sistema funcional. Gabriel Angel de Jesus Rumani detalla que el programa utilizará Flask de Python para el componente visual y el servidor, una base de datos SQLite 3 por la baja complejidad de sus tablas, soporte para adjuntar archivos en formatos PDF, texto, CSV y Excel, y la función de conversión de voz a texto ("speech to text") para la carga mediante audio ([00:00:01](?tab=t.x0kwtoxcmpj6#heading=h.pajqeyz11c9)). Además, Gabriel Angel de Jesus Rumani señala que se requiere una llave API de un modelo de lenguaje para la demostración ([00:25:42](?tab=t.x0kwtoxcmpj6#heading=h.eetttjdlj5ee)).

* **Planificación del desarrollo y pruebas locales**: Se discute la estructuración del proceso de desarrollo y la evaluación del sistema en el equipo del usuario desarrollador. Gabriel Angel de Jesus Rumani propone utilizar la arquitectura de desarrollo guiado por especificaciones para establecer una planificación clara y ajustable. Gonzalo D'Oliveira Lima tiene como tarea pedirle a la sesión en la nube que levante la aplicación, obteniendo una dirección URL local para verificar traducciones, adjuntar archivos y comprobar la estabilidad de la herramienta ([00:01:04](?tab=t.x0kwtoxcmpj6#heading=h.rapvddeggvx2)). Posteriormente, Gonzalo D'Oliveira Lima puede devolver el informe de errores y observaciones a la sesión para que el agente adapte el contexto y las instrucciones ([00:02:30](?tab=t.x0kwtoxcmpj6#heading=h.gpff3qeidbl9)).

* **Publicación de la aplicación en un servidor web gratuito**: Gonzalo D'Oliveira Lima consulta la posibilidad de migrar la aplicación desde el entorno local hacia un servidor web para poder acceder desde un teléfono celular o cualquier ubicación ([00:02:30](?tab=t.x0kwtoxcmpj6#heading=h.gpff3qeidbl9)). Gabriel Angel de Jesus Rumani explica que, dado que se trata de un uso personal y no de un aplicativo productivo, se requerirá un repositorio en GitHub o GitLab para utilizar servicios de alojamiento gratuitos compatibles con ese flujo. Una vez que el programa se encuentre testeado en local, se guarda en el repositorio y el servidor seleccionado procede a publicarlo para que se acceda mediante un enlace web público ([00:03:42](?tab=t.x0kwtoxcmpj6#heading=h.enwgx7ovn3x1)).

*Revisa las notas de Gemini para asegurarte de que sean precisas. [Obtén sugerencias y descubre cómo Gemini toma notas](https://support.google.com/meet/answer/14754931)*

*Cómo es la calidad de **estas notas específicas?** [Responde una breve encuesta](https://google.qualtrics.com/jfe/form/SV_5bXzKQfylMIhSXc?confid=53XtE_eQmMiSXnB6JkfcDxIQOBEBMgUIigIgABgFCA&detailLevel=standard&hasImages=False&entryPoint=footerMain&isGoogler=False) para darnos tu opinión; por ejemplo, cuán útiles te resultaron las notas.*