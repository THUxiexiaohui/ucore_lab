# Lab1 erport

计23班
谢晓晖
2012011315

## [练习1]

[练习1.1] 操作系统镜像文件 ucore.img 是如何一步一步生成的?(需要比较详细地解释 Makefile 中
每一条相关命令和命令参数的含义,以及说明命令导致的结果)
>  * 参考了答案

```
bin/ucore.img
| 生成ucore.img的相关代码为
| $(UCOREIMG): $(kernel) $(bootblock)
|	$(V)dd if=/dev/zero of=$@ count=10000
|	$(V)dd if=$(bootblock) of=$@ conv=notrunc
|	$(V)dd if=$(kernel) of=$@ seek=1 conv=notrunc
|
| 为了生成ucore.img，首先需要生成bootblock、kernel
|
|>	bin/bootblock
|	| 生成bootblock的相关代码为
|	| $(bootblock): $(call toobj,$(bootfiles)) | $(call totarget,sign)
|	|	@echo + ld $@
|	|	$(V)$(LD) $(LDFLAGS) -N -e start -Ttext 0x7C00 $^ \
|	|		-o $(call toobj,bootblock)
|	|	@$(OBJDUMP) -S $(call objfile,bootblock) > \
|	|		$(call asmfile,bootblock)
|	|	@$(OBJCOPY) -S -O binary $(call objfile,bootblock) \
|	|		$(call outfile,bootblock)
|	|	@$(call totarget,sign) $(call outfile,bootblock) $(bootblock)
|	|
|	| 为了生成bootblock，首先需要生成bootasm.o、bootmain.o、sign
|	|
|	|>	obj/boot/bootasm.o, obj/boot/bootmain.o
|	|	| 生成bootasm.o,bootmain.o的相关makefile代码为
|	|	| bootfiles = $(call listf_cc,boot) 
|	|	| $(foreach f,$(bootfiles),$(call cc_compile,$(f),$(CC),\
|	|	|	$(CFLAGS) -Os -nostdinc))
|	|	| 实际代码由宏批量生成
|	|	| 
|	|	| 生成bootasm.o需要bootasm.S
|	|	| 实际命令为
|	|	| gcc -Iboot/ -fno-builtin -Wall -ggdb -m32 -gstabs \
|	|	| 	-nostdinc  -fno-stack-protector -Ilibs/ -Os -nostdinc \
|	|	| 	-c boot/bootasm.S -o obj/boot/bootasm.o
|	|	| 其中关键的参数为
|	|	| 	-ggdb  生成可供gdb使用的调试信息。这样才能用qemu+gdb来调试bootloader or ucore。
|	|	|	-m32  生成适用于32位环境的代码。我们用的模拟硬件是32bit的80386，所以ucore也要是32位的软件。
|	|	| 	-gstabs  生成stabs格式的调试信息。这样要ucore的monitor可以显示出便于开发者阅读的函数调用栈信息
|	|	| 	-nostdinc  不使用标准库。标准库是给应用程序用的，我们是编译ucore内核，OS内核是提供服务的，所以所有的服务要自给自足。
|	|	|	-fno-stack-protector  不生成用于检测缓冲区溢出的代码。这是for 应用程序的，我们是编译内核，ucore内核好像还用不到此功能。
|	|	| 	-Os  为减小代码大小而进行优化。根据硬件spec，主引导扇区只有512字节，我们写的简单bootloader的最终大小不能大于510字节。
|	|	| 	-I<dir>  添加搜索头文件的路径
|	|	| 
|	|	| 生成bootmain.o需要bootmain.c
|	|	| 实际命令为
|	|	| gcc -Iboot/ -fno-builtin -Wall -ggdb -m32 -gstabs -nostdinc \
|	|	| 	-fno-stack-protector -Ilibs/ -Os -nostdinc \
|	|	| 	-c boot/bootmain.c -o obj/boot/bootmain.o
|	|	| 新出现的关键参数有
|	|	| 	-fno-builtin  除非用__builtin_前缀，
|	|	|	              否则不进行builtin函数的优化
|	|
|	|>	bin/sign
|	|	| 生成sign工具的makefile代码为
|	|	| $(call add_files_host,tools/sign.c,sign,sign)
|	|	| $(call create_target_host,sign,sign)
|	|	| 
|	|	| 实际命令为
|	|	| gcc -Itools/ -g -Wall -O2 -c tools/sign.c \
|	|	| 	-o obj/sign/tools/sign.o
|	|	| gcc -g -Wall -O2 obj/sign/tools/sign.o -o bin/sign
|	|
|	| 首先生成bootblock.o
|	| ld -m    elf_i386 -nostdlib -N -e start -Ttext 0x7C00 \
|	|	obj/boot/bootasm.o obj/boot/bootmain.o -o obj/bootblock.o
|	| 其中关键的参数为
|	|	-m <emulation>  模拟为i386上的连接器
|	|	-nostdlib  不使用标准库
|	|	-N  设置代码段和数据段均可读写
|	|	-e <entry>  指定入口
|	|	-Ttext  制定代码段开始位置
|	|
|	| 拷贝二进制代码bootblock.o到bootblock.out
|	| objcopy -S -O binary obj/bootblock.o obj/bootblock.out
|	| 其中关键的参数为
|	|	-S  移除所有符号和重定位信息
|	|	-O <bfdname>  指定输出格式
|	|
|	| 使用sign工具处理bootblock.out，生成bootblock
|	| bin/sign obj/bootblock.out bin/bootblock
|
|>	bin/kernel
|	| 生成kernel的相关代码为
|	| $(kernel): tools/kernel.ld
|	| $(kernel): $(KOBJS)
|	| 	@echo + ld $@
|	| 	$(V)$(LD) $(LDFLAGS) -T tools/kernel.ld -o $@ $(KOBJS)
|	| 	@$(OBJDUMP) -S $@ > $(call asmfile,kernel)
|	| 	@$(OBJDUMP) -t $@ | $(SED) '1,/SYMBOL TABLE/d; s/ .* / /; \
|	| 		/^$$/d' > $(call symfile,kernel)
|	| 
|	| 为了生成kernel，首先需要 kernel.ld init.o readline.o stdio.o kdebug.o
|	|	kmonitor.o panic.o clock.o console.o intr.o picirq.o trap.o
|	|	trapentry.o vectors.o pmm.o  printfmt.o string.o
|	| kernel.ld已存在
|	|
|	|>	obj/kern/*/*.o 
|	|	| 生成这些.o文件的相关makefile代码为
|	|	| $(call add_files_cc,$(call listf_cc,$(KSRCDIR)),kernel,\
|	|	|	$(KCFLAGS))
|	|	| 这些.o生成方式和参数均类似，仅举init.o为例，其余不赘述
|	|>	obj/kern/init/init.o
|	|	| 编译需要init.c
|	|	| 实际命令为
|	|	|	gcc -Ikern/init/ -fno-builtin -Wall -ggdb -m32 \
|	|	|		-gstabs -nostdinc  -fno-stack-protector \
|	|	|		-Ilibs/ -Ikern/debug/ -Ikern/driver/ \
|	|	|		-Ikern/trap/ -Ikern/mm/ -c kern/init/init.c \
|	|	|		-o obj/kern/init/init.o
|	| 
|	| 生成kernel时，makefile的几条指令中有@前缀的都不必需
|	| 必需的命令只有
|	| ld -m    elf_i386 -nostdlib -T tools/kernel.ld -o bin/kernel \
|	| 	obj/kern/init/init.o obj/kern/libs/readline.o \
|	| 	obj/kern/libs/stdio.o obj/kern/debug/kdebug.o \
|	| 	obj/kern/debug/kmonitor.o obj/kern/debug/panic.o \
|	| 	obj/kern/driver/clock.o obj/kern/driver/console.o \
|	| 	obj/kern/driver/intr.o obj/kern/driver/picirq.o \
|	| 	obj/kern/trap/trap.o obj/kern/trap/trapentry.o \
|	| 	obj/kern/trap/vectors.o obj/kern/mm/pmm.o \
|	| 	obj/libs/printfmt.o obj/libs/string.o
|	| 其中新出现的关键参数为
|	|	-T <scriptfile>  让连接器使用指定的脚本
|
| 生成一个有10000个块的文件，每个块默认512字节，用0填充
| dd if=/dev/zero of=bin/ucore.img count=10000
|
| 把bootblock中的内容写到第一个块
| dd if=bin/bootblock of=bin/ucore.img conv=notrunc
|
| 从第二个块开始写kernel中的内容
| dd if=bin/kernel of=bin/ucore.img seek=1 conv=notrunc
```

[练习1.2] 一个被系统认为是符合规范的硬盘主引导扇区的特征是什么?

>  从sign.c的代码中可以看出符合规范的硬盘主引导扇区特征是：
>  * 磁盘主引导扇区为512字节
>  * 第510个字节是0x55
>  * 第511个字节是0xAA



## [练习2]

[练习2.1] 从 CPU 加电后执行的第一条指令开始,单步跟踪 BIOS 的执行。

 
> * 在makefile中添加内容
```
new_Debug: $(UCOREIMG)
	$(V)$(TERMINAL) -e "$(QEMU) -S -s -d in_asm -D $(BINDIR)/q.log -monitor stdio -hda $< -serial null"
	$(V)sleep 2
	$(V)$(TERMINAL) -e "gdb -q -x tools/new_Debug"
```
> * 新建tools/new_Debug，在里面添加内容
```
file bin/kernel
target remote :1234
set architecture i8086
```
> * 在终端使用命令
```
make new_Debug
```
进入调试模式
> * 使用si命令进行即可进行单步调试


[练习2.2] 在初始化位置0x7c00 设置实地址断点,测试断点正常。

>  * 在tools/new_Debug结尾加上
``` 
	b *0x7c00  
	c          
	x /10i $pc  
```
	
>  * 运行"make new_Debug"便可得到

```
	Breakpoint 1, 0x00007c00 in ?? ()
	=> 0x7c00:	cli    
   	0x7c01:	cld    
   	0x7c02:	xor    %ax,%ax
   	0x7c04:	mov    %ax,%ds
   	0x7c06:	mov    %ax,%es
   	0x7c08:	mov    %ax,%ss
   	0x7c0a:	in     $0x64,%al
   	0x7c0c:	test   $0x2,%al
   	0x7c0e:	jne    0x7c0a
   	0x7c10:	mov    $0xd1,%al

```

[练习2.3] 在调用qemu 时增加-d in_asm -D q.log 参数，便可以将运行的汇编指令保存在q.log 中。
将执行的汇编代码与bootasm.S 和 bootblock.asm 进行比较，看看二者是否一致。

>  * 在终端运行"make new_Debug" 
>  * 并键入"continue"后

>  * 可以在bin/q.log中读到"call bootmain"前执行的命令
```
	0x000fd12d:  cli    
	0x000fd12e:  cld    
	0x000fd12f:  mov    $0x8f,%eax	
	0x000fd135:  out    %al,$0x70
	0x000fd137:  in     $0x71,%al
	0x000fd139:  in     $0x92,%al
	0x000fd13b:  or     $0x2,%al
	0x000fd13d:  out    %al,$0x92
	0x000fd13f:  lidtw  %cs:0x66c0
	0x000fd145:  lgdtw  %cs:0x6680
	0x000fd14b:  mov    %cr0,%eax
	0x000fd14e:  or     $0x1,%eax
	0x000fd152:  mov    %eax,%cr0
	----------------
	IN: 
	0x000fd155:  ljmpl  $0x8,$0xfd15d
	----------------
	IN: 
	0x000fd15d:  mov    $0x10,%eax
	0x000fd162:  mov    %eax,%ds
	----------------
	IN: 
	0x000fd164:  mov    %eax,%es
	----------------
	IN: 
	0x000fd166:  mov    %eax,%ss
	----------------
	IN: 
	0x000fd168:  mov    %eax,%fs
	----------------
	IN: 
	0x000fd16a:  mov    %eax,%gs
	0x000fd16c:  mov    %ecx,%eax
	0x000fd16e:  jmp    *%edx
```

>  * 其与bootasm.S和bootblock.asm中的代码相同。

[练习2.4]自己找一个bootloader或内核中的代码位置，设置断点并进行测试。 

> * 在makefile中添加内容
	```
	new_Debug2: $(UCOREIMG)
		$(V)$(TERMINAL) -e "$(QEMU) -S -s -d in_asm -D $(BINDIR)/q.log -monitor stdio -hda $< -serial null"
		$(V)sleep 2
		$(V)$(TERMINAL) -e "gdb -q -x tools/new_Debug2"
	```
> * 新建tools/new_Debug2，在里面添加内容

	```
	file obj/bootblock.o
	target remote :1234
	b bootmain.c:10
	continue
	```
> * 在终端使用命令进入调试模式，成功跳到断点bootmain.c中的第10行

	```
	make new_Debug2
	```

## [练习3]
分析bootloader 进入保护模式的过程。


>  * 首先清理环境：将flag和段寄存器ds、es、ss置0

```
	.code16
	    cli
	    cld
	    xorw %ax, %ax
	    movw %ax, %ds
	    movw %ax, %es
	    movw %ax, %ss
```

> * 等待8042键盘控制器不忙，将数据0xd1送到端口0x64，将数据0xdf送到端口0x60，开启A20

```
	seta20.1:               
	    inb $0x64, %al       
	    testb $0x2, %al     
	    jnz seta20.1        
	
	    movb $0xd1, %al     
	    outb %al, $0x64     
	
	seta20.1:               
	    inb $0x64, %al       
	    testb $0x2, %al     
	    jnz seta20.1        
	
	    movb $0xdf, %al     
	    outb %al, $0x60    
```

>  * 初始化GDT表

```
	    lgdt gdtdesc
```

> * 使能cr0寄存器的PE位置，从实模式进入保护模式

```
	    movl %cr0, %eax
	    orl $CR0_PE_ON, %eax
	    movl %eax, %cr0
```

> * 跳转到32位地址下的下一条指令

```
	 ljmp $PROT_MODE_CSEG, $protcseg
```

> * 设置保护模式下的段寄存器DS、ES、FS、GS、SS，并建立堆栈

```
	.code32
	protcseg:
	    movw $PROT_MODE_DSEG, %ax
	    movw %ax, %ds
	    movw %ax, %es
	    movw %ax, %fs
	    movw %ax, %gs
	    movw %ax, %ss
	    movl $0x0, %ebp
	    movl $start, %esp
```
> * 跳转到bootmain函数

```
	    call bootmain
```


## [练习4]
分析bootloader加载ELF格式的OS的过程。


>  * 观察readsect函数，

```
	static void
	readsect(void *dst, uint32_t secno) {
	    waitdisk();                          //等待硬盘，准备输出读入配置信息
	
	    outb(0x1F2, 1);                         // 设置读取扇区的数目为1
	    //将32位的磁盘号secno分成四段，每段8位，依次写入0x1F6~0x1F3，其中最高的4位强制设为1110，0表示访问“Disk 0”
	    outb(0x1F3, secno & 0xFF);
	    outb(0x1F4, (secno >> 8) & 0xFF);  
	    outb(0x1F5, (secno >> 16) & 0xFF);
	    outb(0x1F6, ((secno >> 24) & 0xF) | 0xE0);

	    outb(0x1F7, 0x20);                      //将0x20命令写入地址0x1F7，读取扇区
	
	    waitdisk();                            //等待磁盘，准备读入数据

	    insl(0x1F0, dst, SECTSIZE / 4);         // 从地址0x1F0读入数据到指针dst处
	}
```

>  * 观察readseg函数：简单包装了readsect，循环从设备读取任意长度的内容。


>  * 观察bootmain函数

```
	void
	bootmain(void) {
	    // 首先读取ELF的头部
	    readseg((uintptr_t)ELFHDR, SECTSIZE * 8, 0);
	
	    // 取出ELF文件头中的e_magic成员判断是否符合要求
	    if (ELFHDR->e_magic != ELF_MAGIC) {
	        goto bad;
	    }
	
	    struct proghdr *ph, *eph;
	
	    //用ELF文件头中的程序头信息：e_phoff和e_phnum，来创建描述符ph
	    ph = (struct proghdr *)((uintptr_t)ELFHDR + ELFHDR->e_phoff);
	    eph = ph + ELFHDR->e_phnum;
	
	    // 按照描述表将ELF文件中数据载入内存
	    for (; ph < eph; ph ++) {
	        readseg(ph->p_va & 0xFFFFFF, ph->p_memsz, ph->p_offset);
	    }

	    // 根据ELF头部储存的入口信息，进入下一步加载
	    ((void (*)(void))(ELFHDR->e_entry & 0xFFFFFF))();
	
	bad:
	    outw(0x8A00, 0x8A00);
	    outw(0x8A00, 0x8E00);
	    while (1);
	}
```


## [练习5] 
实现函数调用堆栈跟踪函数 
>  * 根据提示：

```
     /* LAB1 YOUR CODE : STEP 1 */
     /* (1) call read_ebp() to get the value of ebp. the type is (uint32_t);
      * (2) call read_eip() to get the value of eip. the type is (uint32_t);
      * (3) from 0 .. STACKFRAME_DEPTH
      *    (3.1) printf value of ebp, eip
      *    (3.2) (uint32_t)calling arguments [0..4] = the contents in address (unit32_t)ebp +2 [0..4]
      *    (3.3) cprintf("\n");
      *    (3.4) call print_debuginfo(eip-1) to print the C calling function name and line number, etc.
      *    (3.5) popup a calling stackframe
      *           NOTICE: the calling funciton's return addr eip  = ss:[ebp+4]
      *                   the calling funciton's ebp = ss:[ebp]
      */
```
>  * 完成如下代码，在代码编写中发现需要判断ebp是否为0，否则会不断输出，同时需要在for循环外对变量进行初始化，在for循环内部初始化会报错

```
   uint32_t ebp = read_ebp();
    uint32_t eip = read_eip();
    int i,j;
    for (i = 0; i < STACKFRAME_DEPTH; i ++) {
	if (ebp == 0x00000000) break;
        cprintf("ebp:0x%08x eip:0x%08x args:", ebp, eip);
        for (j = 0; j < 4; j ++) {
            cprintf("0x%08x ", (uint32_t *)ebp + 2);
        }
        cprintf("\n");
        print_debuginfo(eip - 1);
        eip = ((uint32_t *)ebp)[1];
        ebp = ((uint32_t *)ebp)[0];
    }
```




## [练习6]
完善中断初始化和处理

[练习6.1] 中断向量表中一个表项占多少字节？其中哪几位代表中断处理代码的入口？

> * 查看mmu.h中的结构gatedesc，可知一个表项占8字节
> * 中断描述符gatedesc中，0~15位表示段偏移量低16位，16~31位表示段描述符，48~63位表示段偏移量高16位，这些数据共同描述了中断处理代码的入口


[练习6.2] 请编程完善kern/trap/trap.c中对中断向量表进行初始化的函数idt_init。

>  * 根据提示：

```
     /* LAB1 YOUR CODE : STEP 2 */
     /* (1) Where are the entry addrs of each Interrupt Service Routine (ISR)?
      *     All ISR's entry addrs are stored in __vectors. where is uintptr_t __vectors[] ?
      *     __vectors[] is in kern/trap/vector.S which is produced by tools/vector.c
      *     (try "make" command in lab1, then you will find vector.S in kern/trap DIR)
      *     You can use  "extern uintptr_t __vectors[];" to define this extern variable which will be used later.
      * (2) Now you should setup the entries of ISR in Interrupt Description Table (IDT).
      *     Can you see idt[256] in this file? Yes, it's IDT! you can use SETGATE macro to setup each item of IDT
      * (3) After setup the contents of IDT, you will let CPU know where is the IDT by using 'lidt' instruction.
      *     You don't know the meaning of this instruction? just google it! and check the libs/x86.h to know more.
      *     Notice: the argument of lidt is idt_pd. try to find it!
      */
```
>  * 可完成如下代码，注意到系统调用中断权限为用户态权限，需要与其他中断区分开来

```
extern uintptr_t __vectors[];
	int i;
	for (i = 0; i < 256; ++i) {
		if (i == T_SYSCALL) {
			SETGATE(idt[i], 1, GD_KTEXT, __vectors[i], DPL_USER);
		} else if (i == T_SWITCH_TOK) {
			SETGATE(idt[i], 0, GD_KTEXT, __vectors[i], DPL_USER);
		} else {
			SETGATE(idt[i], 0, GD_KTEXT, __vectors[i], DPL_KERNEL);
		}
	}
	lidt(&idt_pd);
```

[练习6.3] 请编程完善trap.c中的中断处理函数trap，在对时钟中断进行处理的部分填写trap函数

>  * 根据提示可得如下代码：

```
 		ticks ++;
        if (ticks % TICK_NUM == 0) {
            print_ticks();
        }
        break;
```


## [练习7]

增加syscall功能，即增加一用户态函数（可执行一特定系统调用：获得时钟计数值），
当内核初始完毕后，可从内核态返回到用户态的函数，而用户态的函数又通过系统调用得到内核态的服务

在idt_init中，将用户态调用SWITCH_TOK中断的权限打开。
	SETGATE(idt[T_SWITCH_TOK], 1, KERNEL_CS, __vectors[T_SWITCH_TOK], 3);

在trap_dispatch中，将iret时会从堆栈弹出的段寄存器进行修改
	对TO User
```
	    tf->tf_cs = USER_CS;
	    tf->tf_ds = USER_DS;
	    tf->tf_es = USER_DS;
	    tf->tf_ss = USER_DS;
```
	对TO Kernel

```
	    tf->tf_cs = KERNEL_CS;
	    tf->tf_ds = KERNEL_DS;
	    tf->tf_es = KERNEL_DS;
```

在lab1_switch_to_user中，调用T_SWITCH_TOU中断。
注意从中断返回时，会多pop两位，并用这两位的值更新ss,sp，损坏堆栈。
所以要先把栈压两位，并在从中断返回后修复esp。
```
	asm volatile (
	    "sub $0x8, %%esp \n"
	    "int %0 \n"
	    "movl %%ebp, %%esp"
	    : 
	    : "i"(T_SWITCH_TOU)
	);
```

在lab1_switch_to_kernel中，调用T_SWITCH_TOK中断。
注意从中断返回时，esp仍在TSS指示的堆栈中。所以要在从中断返回后修复esp。
```
	asm volatile (
	    "int %0 \n"
	    "movl %%ebp, %%esp \n"
	    : 
	    : "i"(T_SWITCH_TOK)
	);
```

但这样不能正常输出文本。根据提示，在trap_dispatch中转User态时，将调用io所需权限降低。
```
	tf->tf_eflags |= 0x3000;
```


