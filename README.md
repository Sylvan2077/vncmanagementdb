# VNCManagementDB

VNCManagementDB 是一个基于Django框架开发的Web后端应用，主要用于管理NoVNC的启动、关闭、OTP密码重置等。 

VNCManagementDB在设计上采用前后端分离的技术来实现，其中前端使用 `Vue.js` 来编写，后端使用 `Django` 来提供服务，数据库使用了 `PostgreSQL` 和 `Redis` ，其中 `PostgreSQL` 用作数据存储， `Redis` 用作 `session` 保存等功能。
VNCManagementDB在功能上，分为前台和后台两个部分，其中前台主要进行用户的登录、茉莉平台APP的启动、产品手册的展示等；后台是该系统的管理员需要在系统安装部署后管理并维护系统的操作，具体工作包括：1. 系统基本信息设置； 2. 系统用户的管理； 3. APP的管理；4. 系统公告的发布和管理； 5. 系统用户启动软件的管理等工作。具体的页面这里就不再详细介绍，请直接启动体验使用即可。

下面简要介绍如何基于本代码进行二次开发以及制作镜像。

## 二次开发步骤

### 安装依赖包

#### Python 相关依赖

因为本程序是基于 `Django` 进行开发的，所以需要安装好相应的依赖包，另外本项目当前是基于 Python 3 进行开发，所以请在机器中安装好 `Python 3` 。

另外，对于本项目需要安装的软件包，可以在 `deploy/requirements.txt` 中看到。

为了开发方便，建议在虚拟环境中进行开发，当前推荐使用 `virtualenv` 来管理虚拟环境，
另外也可再安装 `virtualenvwrapper` 来更方便地创建、使用虚拟环境。

> 注意在创建虚拟环境时，最好指定使用的 Python 版本大于 2。

在创建好虚拟环境并进入虚拟环境后，再使用 `pip install -r deploy/requirements.txt` 将所需的依赖包安装上。

#### docker 相关依赖

另外，为了方便，数据库由相应 docker 容器来提供，这些镜像借助 `docker-compose` 工具来进行启动，
所以需要先安装配置好 `docker` 和 `docker-compose` 工具。

> 注： `docker-compose` 也可以直接到[其 GitHub 发布页](*https://github.com/docker/compose/releases*)下载编译后的单个二进制文件来使用。

> 注：如果不想使用 `docker` 来提供数据库，也可以直接使用现有安装的数据库，在启动时，可以参考 `apps/novncdb/production_settings.py` 中对数据库的设定，相应修改 `apps/novncdb/develop_settings.py` 中的设定。

### 具体开发

在安装好上述依赖后，可以直接使用 `docker-compose deploy/develop/docker-compose.yml` 来启动相应的数据库容器。

如果启动失败，请检测 `docker-compose.yml` 文件中定义的网络端口是否被占用。

接着再按照业务，进行相应的修改。

如果需要进行测试，在开发时，可以直接使用 `Django` 内置的服务程序进行测试，主要命令为：

``` *bash
*work paradb # 进入虚拟环境，paradb 为虚拟环境名称
python manage.py runserver 10086 # 启动服务程序，其中的 10086 为服务端口，可以根据需要指定
```

### 制作镜像

在代码开发并测试无误后，便可以进行部署时所用镜像的制作了。

为了方便，在本项目的代码中已经包含了一个 `Dockerfile` 用来制作镜像，只需要执行 `docker build -t paradb_backend .` 就可以制作镜像了。
其中 `-t` 选项指定制作后镜像的 tag，可以根据需要进行更改。